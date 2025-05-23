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

def update_json(filename = "artists.json"):
    
    """
    Ouverture de la base de données JSON et récupération des artistes en ligne.
    """
    print(f"[{this_name}] Ouverture de la base de données...")
    artistes = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                artistes = json.load(f)
            except json.JSONDecodeError:
                print(f"[{this_name}] ⚠️ Erreur : le fichier JSON est mal formé.")
    
    """
    Récupération des artistes en ligne depuis Spotify grâce à l'API via spotify.py. Sauvegarde de cette liste dans un autre fichier.
    """
    print(f"[{this_name}] Récupération des artistes en ligne sur spotify...")
    new_artistes_spotify = spotify.get_artists()
    f = open("artists_list.txt", "w", encoding="utf-8")
    for artiste in new_artistes_spotify:
        f.write(f"{artiste['name']}\n")
    f.close()
    print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes_spotify)} artistes récupérés via spotify.")
    
    """
    Récupération des artistes en ligne depuis Musicbrainz grâce à l'API via musicbrainz.py. Sauvegarde de cette liste dans un autre fichier.
    """
    print(f"[{this_name}] Récupération des artistes en ligne sur musicbrainz...")
    new_artistes_musicbrainz = musicbrainz.get_artists()
    print(f"[{this_name}] Récupération des artistes en ligne sur spotify...")
    new_artistes_spotify = spotify.get_artists()
    f = open("artists_list.txt", "w", encoding="utf-8")
    for artiste in new_artistes_spotify:
        f.write(f"{artiste['name']}\n")
    f.close()
    print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes_spotify)} artistes récupérés via spotify.")
    
    """
    Récupération des artistes en ligne depuis Musicbrainz grâce à l'API via musicbrainz.py. Sauvegarde de cette liste dans un autre fichier.
    """
    print(f"[{this_name}] Récupération des artistes en ligne sur musicbrainz...")
    new_artistes_musicbrainz = musicbrainz.get_artists()
    print(f"[{this_name}] Récupération des artistes en ligne...")
    new_artistes = spotify.get_artists()

    '''
    # Sauvegarde de la liste des artistes dans un fichier texte
    f = open("artists_list.txt", "w", encoding="utf-8")
    for artiste in new_artistes_musicbrainz:
        f.write(f"{artiste['name']}\n")
    f.close()
    print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes_musicbrainz)} artistes récupérés via musicbrainz.")
    
    '''
    print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes)} artistes récupérés.")

    """
    Rajout de ces artistes à notre base de données JSON.
    """
    print(f"[{this_name}] Mise à jour de la base de données...")
    for artiste in new_artistes_spotify:
        if not any(a['name'] == artiste['name'] for a in artistes):
            # Ajouter l'artiste à la liste
            artistes.append(artiste)
            print(f"[{this_name}] Ajout de l'artiste : {artiste['name']} {' '*100}", end='\r')
        else:
            print(f"[{this_name}] Artiste mis à jour : {artiste['name']} {' '*100}", end='\r')
    for artiste in new_artistes_musicbrainz:
        if not any(a['name'] == artiste['name'] for a in artistes):
            # Ajouter l'artiste à la liste
            artistes.append(artiste)
            print(f"[{this_name}] Ajout de l'artiste : {artiste['name']} {' '*100}", end='\r')
            print(f"[{this_name}] Ajout de l'artiste : {artiste['name']} {' '*100}", end='\r')
        else:
            print(f"[{this_name}] Artiste mis à jour : {artiste['name']} {' '*100}", end='\r')
            print(f"[{this_name}] Artiste mis à jour : {artiste['name']} {' '*100}", end='\r')
    """
    Mise à jour des liens Genius, Last-FM, MusicBrainz... pour chaque artiste.
    """
    fails = []
    print(f"[{this_name}] Mise à jour des liens... {' '*100}")
    print(f"[{this_name}] Mise à jour des liens... {' '*100}")
    length = len(artistes)
    i = 0
    for artiste in artistes:
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {' '*100}", end='\r')
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {' '*100}", end='\r')
        rep_genius = genius.get_artist_id_by_name(artiste['name']+" ")
        if rep_genius is None:
            print(f"[{this_name}] Impossible de trouver l'artiste : {artiste['name']}")
            fails.append(artiste['name'])
            continue
        else:
            _, artiste['id_genius'] , artiste['url_genius'] = rep_genius
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {' '*100}", end='\r')
        object_or_None = genius.get_artist_id_by_name(artiste['name'])
        if object_or_None is None:
            print(f"[{this_name}] Impossible de trouver l'artiste {artiste['name']}")
            continue
        else :
            _, artiste['id_genius'] , artiste['url_genius'], _= object_or_None
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {' '*100}", end='\r')
        object_or_None = genius.get_artist_id_by_name(artiste['name'])
        if object_or_None is None:
            print(f"[{this_name}] Impossible de trouver l'artiste {artiste['name']}")
            continue
        else :
            _, artiste['id_genius'] , artiste['url_genius'], _= object_or_None
        artiste['id_mb'] = musicbrainz.get_artist_id_by_name(artiste['name'])
        i+=1
        
    """
    Sauvegarde de la base de données JSON.
    """
    print(f"[{this_name}] Écriture dans la base de données... {' '*100}")
    print(f"[{this_name}] Écriture dans la base de données... {' '*100}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artistes, f, indent=2, ensure_ascii=False)
    print(f"[{this_name}] Fermeture de la base de données...")


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
    client.close()
    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    return fails

# def filter_artists(artist_names, min_listeners=10000):
#     """
#     Filtre les artistes ayant au moins `min_listeners` auditeurs mensuels sur Spotify.
#     Args:
#         artist_names (list): Liste de noms d'artistes (str).
#         min_listeners (int): Seuil minimal d'auditeurs mensuels.
    
#     Returns:
#         list: Liste d'artistes ayant au moins `min_listeners` auditeurs.
#     """
#     valid_artists = []
#     for name in artist_names:
#         try:
#             listeners = spotify.get_monthly_listeners(name)
#             if listeners is not None and listeners >= min_listeners:
#                 valid_artists.append(name)
#             else:
#                 print(f"[update.py] {name} n'a pas assez d'auditeurs ({listeners})")
#         except Exception as e:
#             print(f"[update.py] ⚠️ Erreur pour {name} : {e}")
#     return valid_artists


# def filter_artists(artist_names, min_listeners=10000):
#     """
#     Filtre les artistes ayant au moins `min_listeners` auditeurs mensuels sur Spotify.
#     Args:
#         artist_names (list): Liste de noms d'artistes (str).
#         min_listeners (int): Seuil minimal d'auditeurs mensuels.
    
#     Returns:
#         list: Liste d'artistes ayant au moins `min_listeners` auditeurs.
#     """
#     valid_artists = []
#     for name in artist_names:
#         try:
#             listeners = spotify.get_monthly_listeners(name)
#             if listeners is not None and listeners >= min_listeners:
#                 valid_artists.append(name)
#             else:
#                 print(f"[update.py] {name} n'a pas assez d'auditeurs ({listeners})")
#         except Exception as e:
#             print(f"[update.py] ⚠️ Erreur pour {name} : {e}")
#     return valid_artists


def update_json_to_mongo(filename = "artists.json"):
    """
    This function updates the data in the MongoDB database.
    """
    pass
    print(f"[{this_name}] Ouverture de la base de données...")
    client = MongoClient("mongodb://localhost:27017/")
    '''
    localhost : signifie "ma propre machine" (équivalent de 127.0.0.1).
    mongodb:// : indique que nous utilisons le protocole MongoDB.
    27017 : c’est le port par défaut utilisé par un serveur MongoDB local.
    '''
    db = client["musicdb"]
    collection = db["artists"]

    # Suppression de tous les documents existants
    collection.delete_many({})

    # Chargement des artistes depuis le fichier JSON
    with open(filename, "r", encoding="utf-8") as f:
        artistes = json.load(f)

    # Insertion des artistes dans la base de données
    collection.insert_many(artistes)

def update_featurings_and_songs_to_mongo():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["musicdb"]
    artists_col = db["artists"]
    songs_col = db["songs"]
    featurings_col = db["featurings"]

    # Pour faire correspondre un nom à un id dans la base en utilisant des dictionnaires
    all_artists = list(artists_col.find({}))
    name_to_id = {artist['name'].lower(): artist['_id'] for artist in all_artists}
    name_to_genius_id = {artist['name'].lower(): artist['id_genius'] for artist in all_artists}

    for i, artist in enumerate(all_artists):
        artist_name = artist['name']
        artist_genius_id = artist['id_genius']
        print(f"🔍 Traitement de l'artiste : {artist_name} ({i} / {len(all_artists)}) {' '*100}")

        try:
            tracks = genius.get_artist_featurings(artist_genius_id, max_pages=50)
        except Exception as e:
            print(f"❌ Erreur pour {artist_name} : {e}")
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
            print(end="\r")
            print(end="\r")

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

if __name__ == "__main__":
    #9+6update()
    #update_json_to_mongo()
    ##update_featurings_and_songs_to_mongo()
    ##update_featurings_and_songs_to_mongo()
    '''
    client = MongoClient("mongodb://localhost:27017")
    db = client["arthur_modal"]
    collection = db["artists"]
    collection.delete_many({})
    '''
    update_mongo("test_pop_followers", update_embeddings=True, force_update=True)