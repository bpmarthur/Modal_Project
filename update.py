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

def update_mongo(db_name = "arthur_modal", search_new_artists = False, update_genius = False, update_musicbrainz=False, update_embeddings = False, force_update = False):
    
    if force_update:
        print(f"[{this_name}] La base de données va être entièrement réinitialisée.")
        rep = int_response(f"[{this_name}] Voulez-vous continuer ? Oui = 1, Non = 0 : ")
        if rep == 0:
            print(f"[{this_name}] Abandon de la mise à jour de la base de données.")
            return
    
    """
    Ouverture de la base de données Mongo.
    """
    print(f"[{this_name}] Ouverture de la base de données MongoDB...")
    client = MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db["artists"]
    
    if search_new_artists:
        """
        Récupération des artistes en ligne depuis Spotify grâce à l'API via spotify.py.
        """
        print(f"[{this_name}] Récupération des artistes spotify en ligne...")
        new_artistes_spotify = spotify.get_artists()
        print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes_spotify)} artistes récupérés sur spotify.")

        """
        Récupération des artistes en ligne depuis Musicbrainz grâce à l'API via musicbrainz.py.
        """
        print(f"[{this_name}] Récupération des artistes musicbrainz en ligne...")
        new_artistes_musicbrainz = musicbrainz.get_artists()
        print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes_musicbrainz)} artistes récupérés sur musicbrainz.")

        """
        Filtrage des artistes pour ne garder que ceux qui sont pertinents (nombre d'auditeurs minimum, genre musical, etc...)
        """
        new_artistes = new_artistes_spotify + new_artistes_musicbrainz
        """
        Suppression des doublons par nom d'artiste (insensible à la casse)
        """
        print(f"[{this_name}] Filtrage des artistes récupérés...")
        seen = set()
        unique_artistes = []
        for artiste in new_artistes:
            name = artiste['name'].strip().lower()
            if name not in seen:
                unique_artistes.append(artiste)
                seen.add(name)
        
        filtre_unique_artistes = []
        for artiste in unique_artistes:
            followers = spotify.get_followers(artiste['name'])
            if followers is not None and followers >= 1000:
                filtre_unique_artistes.append(artiste)
        unique_artistes = filtre_unique_artistes
        
        new_artistes = [] # Artistes pas encore dans la BDD !!
        for artiste in unique_artistes:
            # Vérifie si l'artiste est déjà présent dans MongoDB
            if collection.find_one({"name": {"$regex": f"^{re.escape(name)}$", "$options": "i"}}):
                continue  # l'artiste est déjà dans la BDD
            new_artistes.append(artiste)
        

        print(f"[{this_name}] Filtrage des artistes terminé. {len(unique_artistes)} artistes conservés au total.")
        print(f"[{this_name}] {len(new_artistes)} nouveaux artistes rencontrés.")
        '''
        # Sauvegarde de la liste des artistes dans un fichier texte
        '''
        f = open("artists_list.txt", "w", encoding="utf-8")
        for artiste in unique_artistes:
            f.write(f"{artiste['name']}\n")
        f.close()
        longueur = len(unique_artistes)
        """
        Rajout de ces artistes à notre base de données MongoDB.
        """
        print(f"[{this_name}] Mise à jour de la base de données...")
        i = 0
        for artiste in new_artistes:
            i+=1
            print(f"[{this_name}] [{i}/{longueur}] Mise à jour de l'artiste : {artiste['name']} {' '*100}", end='\r')
            collection.update_one({"name": artiste['name']}, {"$setOnInsert": {"name": artiste['name']}}, upsert=True)
        print(f"[{this_name}] Mise à jour de la base de données terminée. {i} artistes mis à jour.")
    """
    Mise à jour des liens Genius, Last-FM, MusicBrainz... pour chaque artiste.
    """

    fails = []
    print(f"[{this_name}] Mise à jour des liens... {' '*100}")
    length = collection.count_documents({})
    i = 0
    for artiste in collection.find():
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {' '*100}", end='\r')
        if update_genius:
            if "id_genius" not in artiste:
                rep_genius = genius.get_artist_id_by_name(artiste['name'])
                if rep_genius is None:
                    print(f"[{this_name}] Impossible de trouver l'artiste : {artiste['name']}")
                    fails.append(artiste)
                    continue
                else:
                    '''
                    Mise à jour de l'artiste en entier
                    _, artiste['id_genius'] , artiste['url_genius'] = rep_genius
                    '''
                    '''
                    Mise à jour de l'artiste en partie
                    '''
                    collection.update_one({"name": artiste['name']}, {"$set": {"id_genius": rep_genius[1], "url_genius": rep_genius[2]}})
        
        if update_embeddings:
            if "id_genius" in artiste and ("embedding" not in artiste or artiste['embedding'] == None):
                    """
                    Calcul du vecteur d'embedding de l'artiste
                    """
                    artist_id = artiste['id_genius']
                    vect = embeddings.get_artist_vector(artist_id, model, max_songs=5)
                    if vect is not None:
                        vect = vect.tolist() 
                        collection.update_one({"name": artiste['name']}, {"$set": {"embedding": vect}})
                

        if update_musicbrainz:
            if "id_mb" not in artiste:
                id_mb = musicbrainz.get_artist_id_by_name(artiste['name'])
                if id_mb != None:
                    collection.update_one({"name": artiste['name']}, {"$set": {"id_mb": id_mb}})
        i+=1

    '''
    Mise à jour des fails
    '''
    if len(fails) > 0:
        rep = ""
        while True:
            rep = input(f"[{this_name}] Il y a {len(fails)} fails. Voulez-vous les mettre à jour ? Oui = 1, Non = 0 : ")
            try:
                rep = int(rep)
                break  # Si ça marche, on sort de la boucle
            except ValueError:
                print("Ce n'est pas un entier valide. Réessayez.")
        if rep == 1:
            print(f"[{this_name}] Mise à jour des fails")
            for artist_fail in fails:
                print(f"[{this_name}] Mise à jour de l'artiste : {artist_fail['name']} {' '*100}")
                rep_genius = genius.get_artist_id_by_name_manual()
                if rep_genius is not None:
                    collection.update_one({"name": artist_fail['name']}, {"$set": {"id_genius": rep_genius[1], "url_genius": rep_genius[2]}})
        else:
            print(f"[{this_name}] Pas de mise à jour des fails {' '*100}")
    else:
        print(f"[{this_name}] Pas de fails {' '*100}")
    """
    Sauvegarde de la base de données JSON.
    """
    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    client.close()
    print(f"[{this_name}] Enregistrement des fails dans fail_update_mongo.txt ...{' '*100}")
    with open("fail_update_mongo.txt", "w", encoding="utf-8") as f:
        for fail in fails:
            f.write(fail['name'] + "\n")

def update_featurings_and_songs_to_mongo(db_name = "arthur_modal"):
    print(f"[{this_name}] Ouverture de la base de données MongoDB...")
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    artists_col = db["artists"]
    featurings_col = db["featurings"]
    fails = []

    # Pour faire correspondre un nom à un id dans la base en utilisant des dictionnaires
    all_artists = list(artists_col.find({}))
    length = len(all_artists)
    name_to_id = {artist['name'].lower(): artist['_id'] for artist in all_artists}
    name_to_genius_id = {artist['name'].lower(): artist['id_genius'] for artist in all_artists}

    for i, artist in enumerate(all_artists):
        artist_name = artist['name']
        artist_genius_id = artist['id_genius']
        print(f"[{this_name}] [{i}/{length}] Traitement de l'artiste : {artist_name} {' '*100}", end='\r')

        try:
            tracks = genius.get_artist_featurings(artist_genius_id, max_pages=50)
        except Exception as e:
            
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
            print(f"[{this_name}] Erreur pour {artist_name} : {e}")
            fails.append(artist_name)
            continue

        for track in tracks:
            song_id = track[0]
            title = track[1]
            artist_names = [musicbrainz.normalize_string(a) for a in track[2]]

            # # Enregistrement dans songs (avec upsert pour éviter les doublons)
            # songs_col.update_one(
            #     {"_id": song_id},
            #     {"$setOnInsert": {"_id": song_id, "title": title}, },
            #     upsert=True
            # )

            # Enregistrement dans featurings (avec upsert pour éviter les doublons)
                
            nb_artistes_presents = 0
            artistes_presents_id = []
            artistes_presents_name = []
            for artist in artist_names:
                artist_id = name_to_id.get(artist)
                if artist_id:
                    artistes_presents_id.append(artist_id)
                    artistes_presents_name.append(artist)
                    nb_artistes_presents += 1
            if nb_artistes_presents >= 2:   
                featurings_col.update_one(
                    {"_id": song_id},
                    {
                        "$setOnInsert": {
                            "_id": int(song_id),
                            "title": title,
                            "artists_id": artistes_presents_id,
                            "artists_names": artistes_presents_name,
                            "artists_genius_id": [name_to_genius_id[artist] for artist in artistes_presents_name]
                        }
                    },
                    upsert=True
                )
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
    
def update_featurings_and_songs_to_mongo_v2(db_name = "arthur_modal"):
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

def final_update(db_name = "data_final", former_db_name = "arthur_modal", search_new_artists = False, update_genius = False, update_musicbrainz=False, update_embeddings = False):
    
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

    '''
    Mise à jour des fails
    '''
    """
    if len(fails) > 0:
        rep = ""
        while True:
            rep = input(f"[{this_name}] Il y a {len(fails)} fails. Voulez-vous les mettre à jour ? Oui = 1, Non = 0 : ")
            try:
                rep = int(rep)
                break  # Si ça marche, on sort de la boucle
            except ValueError:
                print("Ce n'est pas un entier valide. Réessayez.")
        if rep == 1:
            print(f"[{this_name}] Mise à jour des fails")
            for artist_fail in fails:
                print(f"[{this_name}] Mise à jour de l'artiste : {artist_fail['name']} {' '*100}")
                rep_genius = genius.get_artist_id_by_name_manual()
                if rep_genius is not None:
                    collection.update_one({"name": artist_fail['name']}, {"$set": {"id_genius": rep_genius[1], "url_genius": rep_genius[2]}})
        else:
            print(f"[{this_name}] Pas de mise à jour des fails {' '*100}")
    else:
        print(f"[{this_name}] Pas de fails {' '*100}")
    """
    
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

def fail_update_mongo(filename = "fail_final_update_mongo.txt", db_name = "arthur_modal"):
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


def update_json_to_mongo(db_name, filename = "clean_artists.json"):
    """
    This function updates the data in the MongoDB database.
    """
    print(f"[{this_name}] Ouverture de la base de données...")
    client = MongoClient("mongodb://localhost:27017/")
    '''
    localhost : signifie "ma propre machine" (équivalent de 127.0.0.1).
    mongodb:// : indique que nous utilisons le protocole MongoDB.
    27017 : c’est le port par défaut utilisé par un serveur MongoDB local.
    '''
    db = client[db_name]
    collection = db["artists"]

    # Suppression de tous les documents existants
    collection.delete_many({})

    # Chargement des artistes depuis le fichier JSON
    with open(filename, "r", encoding="utf-8") as f:
        artistes = json.load(f)

    # Insertion des artistes dans la base de données
    collection.insert_many(artistes)

def update_csv_to_mongo(db_name, filename = "arthur_fou_db.artists.csv"):
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
    final_update(db_name = "final_db_3", update_embeddings=True)
    #fail_update_mongo(filename = "fail_final_update_mongo.txt", db_name = "arthur_fou_db")
    
    #update_csv_to_mongo(db_name = "final_db")
    #update_featurings_and_songs_to_mongo(db_name = "final_db")
    #update_csv_to_mongo(db_name = "final_db_2")
    #update_featurings_and_songs_to_mongo_v2(db_name = "final_db_2")
    # update_csv_to_mongo(db_name = "final_db_3")
    #update_featurings_and_songs_to_mongo_v2(db_name = "final_db_3")
