import sys
import json
import os
import spotify
import genius
import csv
import time
import musicbrainz
from pymongo import MongoClient
from tools import get_key, int_response
from bson.objectid import ObjectId
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

def fail_update_mongo(db_name = "arthur_modal"):
    print(f"[{this_name}] Ouverture de la base de données MongoDB...")
    client = MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db["artists"]
    print(f"[{this_name}] Récupération des artistes dont la récupération des données a échouée.")
    fails = []
    with open("noms_artistes.txt", "r", encoding="utf-8") as f:
        fails = [line.strip() for line in f.readlines()]

    print(f"[{this_name}] Mise a jour des fails... {' '*100}")
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
                print(f"[{this_name}] Mise à jour de l'artiste : {artist_fail} {' '*100}")
                rep_genius = genius.get_artist_id_by_name_manual()
                if rep_genius is not None:
                    collection.update_one({"name": artist_fail}, {"$set": {"id_genius": rep_genius[1], "url_genius": rep_genius[2]}})
                    fails.remove(artist_fail)
        else:
            print(f"[{this_name}] Pas de mise à jour des fails {' '*100}")
    else:
        print(f"[{this_name}] Pas de fails {' '*100}")

    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    client.close()
    print(f"[{this_name}] Enregistrement des fails restants dans fail_update_mongo.txt ...{' '*100}")
    with open("fail_update_mongo.txt", "w", encoding="utf-8") as f:
        for fail in fails:
            f.write(fail['name'] + "\n")

def update_featurings_and_songs_to_mongo(db_name = "arthur_modal"):
    print(f"[{this_name}] Ouverture de la base de données MongoDB...")
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    artists_col = db["artists"]
    songs_col = db["songs"]
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
                    {"$setOnInsert": {"_id": song_id, "title": title, "artists_id": artistes_presents_id},
                     "artists_names": artistes_presents_name, "artists_genius_id": [name_to_genius_id[artist] for artist in artistes_presents_name]},
                    upsert=True
                )
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")

def convert_to_csv(filename = "artists.csv"):
    # Connexion à MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["musicdb"]  # nom de la base de données
    collection = db["artists"]  # nom de la collection

    # Récupération des données des artistes
    artistes = collection.find()

    # Exportation vers un fichier CSV pour Gephi
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "id_spotify", "id_genius", "url_genius", "genres"])  # En-têtes de colonnes
        for artiste in artistes:
            writer.writerow([artiste["name"], artiste["id_spotify"], artiste["id_genius"], artiste["url_genius"], ",".join(artiste["genres"])])  # Données d'artistes

def test_init_db():
    client = MongoClient("mongodb://localhost:27017")
    db = client["musicdb_artists"]
    collection = db["artists"]
    collection.insert_one({"name": "Jul"})
    
    
    
    
def final_update(db_name = "data_final", former_db_name = "arthur_modal", search_new_artists = False, update_genius = False, update_musicbrainz=False, update_embeddings = False, force_update = False):
    
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
                    collection.delete_one({"name": artist['name']})
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
    
    with open("fails.txt", "w", encoding="utf-8") as f:
        for artist in fails:
            f.write(f"{artist['name']}\n")
    
    """
    Sauvegarde de la base de données JSON.
    """
    client.close()
    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    

if __name__ == "__main__":
    final_update(update_embeddings=True)