import sys
import json
import os
import spotify
import genius
import csv
import musicbrainz
from pymongo import MongoClient
from tools import get_key, int_response
import gensim
import embeddings
import re

GENIUS_API_TOKEN = get_key("Client_access_genius")

headers = {
    'Authorization': f'Bearer {GENIUS_API_TOKEN}'
}

this_name = os.path.basename(__file__)

model = gensim.models.Word2Vec.load("Word2Bezbar-large/word2vec.model")

#Met à jour la base de données MongoDB avec les featurings des artistes
def update_featurings_and_songs_to_mongo(db_name):
    print(f"[{this_name}] Ouverture de la base de données MongoDB...")
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    artists_col = db["artists"]
    featurings_col = db["featurings"]
    fails = []

    # Pour faire correspondre un nom à un id dans la base en utilisant des dictionnaires
    all_artists = list(artists_col.find({}))
    length = len(all_artists)
    

    for i, artist in enumerate(all_artists):
        artist_name = artist['name']
        artist_genius_id = artist['id_genius']
        print(f"[{this_name}] [{i}/{length}] Traitement de l'artiste : {artist_name} {' '*100}")

        try:
            tracks = genius.get_artist_featurings_v2(artist_genius_id, max_pages=60)
        except Exception as e:
            
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            print(f"[{this_name}] Erreur pour {artist_name} : {e}")
            fails.append(artist_name)
            continue

        for track in tracks:
            song_id = track[0]
            title = track[1]
            authors_id = track[2]
            """
            print(f"[{this_name}] Traitement de la chanson : {title}")
            for author_id in authors_id:
                print(f"[{this_name}] {author_id}")
            """
            #artist_names = [musicbrainz.normalize_string(a) for a in track[2]]

            # # Enregistrement dans songs (avec upsert pour éviter les doublons)
            # songs_col.update_one(
            #     {"_id": song_id},
            #     {"$setOnInsert": {"_id": song_id, "title": title}, },
            #     upsert=True
            # )

            # Enregistrement dans featurings (avec upsert pour éviter les doublons)
                
            nb_artistes_presents = 0
            artistes_presents_name = []
            artistes_presents_id = []
            real_authors_id = []
            for author_id in authors_id:
                artiste = artists_col.find_one({"id_genius": int(author_id)})
                if artiste is not None:
                    nb_artistes_presents += 1
                    artistes_presents_name.append(artiste['name'])
                    artistes_presents_id.append(artiste['_id'])
                    real_authors_id.append(artiste['id_genius'])
            if nb_artistes_presents >= 2:
                featurings_col.update_one(
                    {"_id": song_id},
                    {
                        "$setOnInsert": {
                            "_id": int(song_id),
                            "title": title,
                            "artists_id": artistes_presents_id,
                            "artists_names": artistes_presents_name,
                            "artists_genius_id": real_authors_id
                        }
                    },
                    upsert=True
                )
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")

#Met à jour la base de données MongoDB avec les artistes récupérés depuis Spotify et Musicbrainz
def update_mongo(db_name, former_db_name = "arthur_modal", search_new_artists = False, update_genius = False, update_musicbrainz=False, update_embeddings = False):
    
    """
    Ouverture de la base de données Mongo.
    """
    print(f"[{this_name}] Ouverture de la base de données MongoDB...")
    client = MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    former_db = client[former_db_name]
    collection = db["artists"]
    former_collection = former_db["artists"]
    
    if search_new_artists:
        """
        Récupération des artistes en ligne depuis Spotify grâce à l'API via spotify.py.
        """
        print(f"[{this_name}] Récupération des artistes spotify en ligne...")
        new_artists_spotify = spotify.get_artists()
        print(f"[{this_name}] Récupération des artistes sur spotify terminée. {len(new_artists_spotify)} artistes récupérés.")

        """
        Récupération des artistes en ligne depuis Musicbrainz grâce à l'API via musicbrainz.py.
        """
        print(f"[{this_name}] Récupération des artistes musicbrainz en ligne...")
        new_artists_musicbrainz = musicbrainz.get_artists()
        print(f"[{this_name}] Récupération des artistes sur musicbrainz terminée. {len(new_artists_musicbrainz)} artistes récupérés.")

        """
        Standardisation du format de new_artists_musicbrainz sur le format de new_artists_spotify
        """
        print(f"[{this_name}] Standardisation du format des artistes...")
        new_artists = new_artists_spotify
        for artist in new_artists_musicbrainz:
            id_spotify, popularity, followers = spotify.get_artist_data(artist['name'])
            if id_spotify is not None:
                new_artists.append({
                    "name": artist['name'],
                    "id_spotify": id_spotify,
                    "popularity": popularity,
                    "followers": followers
                })

        print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artists_musicbrainz)} obtenus avant filtrage.")

        """
        Filtrage des artistes pour ne garder que ceux qui sont pertinents (nombre d'auditeurs minimum, genre musical, etc...)
        """
        """
        Suppression des doublons par nom d'artiste (insensible à la casse)
        """
        print(f"[{this_name}] Filtrage des artistes récupérés...")
        seen = set()
        unique_artists = []
        for artist in new_artists:
            name = artist['name'].strip().lower()
            if name not in seen:
                unique_artists.append(artist)
                seen.add(name)
        new_artists = unique_artists.copy()
        
        filtre_artists = []
        for artist in unique_artists:
            followers = artist.get('followers')
            if followers is not None and followers >= 1000:
                filtre_artists.append(artist)
        new_artists = filtre_artists.copy()

        print(f"[{this_name}] Filtrage des artistes terminé. {len(new_artists)} artistes conservés au total.")
        '''
        # Sauvegarde de la liste des artistes dans un fichier texte
        '''
        f = open("artists_list.txt", "w", encoding="utf-8")
        for artist in new_artists:
            f.write(f"{artist['name']}\n")
        f.close()
        longueur = len(new_artists)
        """
        Rajout de ces artistes à notre base de données MongoDB.
        """
        print(f"[{this_name}] Mise à jour de la base de données...")
        i = 0
        for artist in new_artists:
            i+=1
            print(f"[{this_name}] [{i}/{longueur}] Mise à jour de l'artiste : {artist['name']} {' '*100}", end='\r')
            collection.update_one({"name": artist['name'], "id_spotify": artist['id_spotify'], "followers": artist['followers'], "popularity": artist['popularity']},
                                  {"$setOnInsert": {"name": artist['name'], "id_spotify": artist['id_spotify'], "followers": artist['followers'], "popularity": artist['popularity']}},
                                  upsert=True)
        print(f"[{this_name}] Mise à jour de la base de données terminée. {i} artistes mis à jour.")
    
    """
    Mise à jour des liens Genius, Last-FM, MusicBrainz... pour chaque artiste.
    """

    fails = []
    print(f"[{this_name}] Mise à jour des liens... {' '*100}")
    length = collection.count_documents({})
    i = 0
    for artist in collection.find():
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artist['name'].strip()} {' '*100}", end='\r')
        if update_genius:
            if "id_genius" not in artist:
                rep_genius = genius.get_artist_id_by_name(artist['name'])
                if rep_genius is None:
                    print(f"[{this_name}] Impossible de trouver l'artiste : {artist['name']}")
                    fails.append(artist)
                    continue
                else:
                    collection.update_one({"name": artist['name']}, {"$set": {"id_genius": rep_genius[1], "url_genius": rep_genius[2]}})

        if update_embeddings:
            if "id_genius" in artist and ("embedding" not in artist or artist['embedding'] == None):
                    """
                    Calcul du vecteur d'embedding de l'artiste
                    """
                    artist_id = artist['id_genius']
                    former_artist = former_collection.find_one({"id_genius": artist_id})
                    if former_artist is not None and "embedding" in former_artist:
                        vect = former_artist["embedding"]
                    else:
                        vect = None
                    if vect is None: 
                        vect = embeddings.get_artist_vector(artist_id, model, max_songs=5)
                    if vect is not None:
                        if type(vect) != list:
                            vect = vect.tolist()
                        collection.update_one({"name": artist['name']}, {"$set": {"embedding": vect}})


        if update_musicbrainz:
            if "id_mb" not in artist:
                id_mb = musicbrainz.get_artist_id_by_name(artist['name'])
                if id_mb != None:
                    collection.update_one({"name": artist['name']}, {"$set": {"id_mb": id_mb}})
        i+=1

    print(f" [{this_name}] Nombre d'artiste restants après suppression de ceux qui n'ont pas pu être trouvés : {collection.count_documents({})}")
    
    """
    Sauvegarde des fails dans un fichier extérieur
    """
    print(f"[{this_name}] Enregistrement des fails dans fail_final_update_mongo.txt ...{' '*100}")
    with open("fail_final_update_mongo.txt", "w", encoding="utf-8") as f:
        for artist in fails:
            f.write(f"{artist['name']}\n")
    
    """
    Sauvegarde de la base de données JSON.
    """
    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    client.close()

#Met à jour la base de données MongoDB à partir d'un fichier contenant les fails
def fail_update_mongo(db_name, filename):
    print(f"[{this_name}] Ouverture de la base de données MongoDB...")
    client = MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db["artists"]
    print(f"[{this_name}] Récupération des artistes dont la récupération des données a échouée dans {filename}...")
    fails = []
    new_fails = []
    with open(filename, "r", encoding="utf-8") as f:
        fails = [line.strip() for line in f.readlines()]
    length = len(fails)
    print(f"[{this_name}] {length} fails récupérés dans {filename}...")

    if len(fails) > 0:
        print(f"[{this_name}] Mise à jour des fails")
        i = 1
        for artist in fails:
            print(f"[{this_name}] [{i}/{length}] Mise à jour de l'artiste : {artist} {' '*100}")
            rep_genius = genius.get_artist_id_by_name_manual()
            if rep_genius is not None:
                collection.update_one({"name": artist}, {"$set": {"id_genius": rep_genius[1], "url_genius": rep_genius[2]}})
            else:
                print(f"[{this_name}] {artist} non mis à jour")
                new_fails.append(artist)
            i+=1
    else:
        print(f"[{this_name}] Pas de fails {' '*100}")

    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    client.close()
    print(f"[{this_name}] Enregistrement des fails restants dans fail_update_mongo.txt ...{' '*100}")
    with open(filename, "w", encoding="utf-8") as f:
        for fail in new_fails:
            f.write(fail + "\n")

#Permet de mettre à jour la base de données MongoDB à partir d'un fichier CSV
def update_csv_to_mongo(db_name, filename = "./data/db_artists_clean.csv"):
    """
    This function updates the data in the MongoDB database.
    """
    print(f"[{this_name}] Ouverture de la base de données...")
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    collection = db["artists"]

    # Suppression de tous les documents existants
    collection.delete_many({})
    print(f"[{this_name}] Lecture du fichier CSV...")
    with open(filename, newline=None) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            collection.insert_one({
    "name": row['name'],
    "id_spotify": row['id_spotify'],
    "followers": int(row['followers']),
    "popularity": int(row['popularity']),
    "id_genius": int(row['id_genius']),
    "url_genius": row['url_genius'],
    "id_mb": row.get('id_mb')
            })
    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    client.close()

if __name__ == "__main__":
    #Génération de la base des artistes
    update_mongo(db_name = "final_db", update_embeddings=True)
    fail_update_mongo(db_name = "final_db", filename = "fail_final_update_mongo.txt")
    
    #Récupération des artistes depuis le fichier CSV si nécessaire, après filtrage notamment
    #update_csv_to_mongo(db_name = "final_db")
    
    #Récupération des featurings
    update_featurings_and_songs_to_mongo(db_name = "final_db")