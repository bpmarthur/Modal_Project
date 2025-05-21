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

GENIUS_API_TOKEN = get_key("Client_access_genius")

headers = {
    'Authorization': f'Bearer {GENIUS_API_TOKEN}'
}

this_name = os.path.basename(__file__)

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
    print(f"[{this_name}] Récupération des artistes en ligne...")
    new_artistes = spotify.get_artists()

    '''
    # Sauvegarde de la liste des artistes dans un fichier texte
    f = open("artists_list.txt", "w", encoding="utf-8")
    for artiste in new_artistes:
        f.write(f"{artiste['name']}\n")
    f.close()
    '''
    print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes)} artistes récupérés.")

    """
    Rajout de ces artistes à notre base de données JSON.
    """
    print(f"[{this_name}] Mise à jour de la base de données...")
    for artiste in new_artistes:
        if not any(a['name'] == artiste['name'] for a in artistes):
            # Ajouter l'artiste à la liste
            artistes.append(artiste)
            print(f"[{this_name}] Ajout de l'artiste : {artiste['name']} {" "*100}", end='\r')
        else:
            print(f"[{this_name}] Artiste mis à jour : {artiste['name']} {" "*100}", end='\r')
            
    """
    Mise à jour des liens Genius, Last-FM, MusicBrainz... pour chaque artiste.
    """
    fails = []
    print(f"[{this_name}] Mise à jour des liens... {" "*100}")
    length = len(artistes)
    i = 0
    for artiste in artistes:
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {" "*100}", end='\r')
        rep_genius = genius.get_artist_id_by_name(artiste['name']+" ")
        if rep_genius is None:
            print(f"[{this_name}] Impossible de trouver l'artiste : {artiste['name']}")
            fails.append(artiste['name'])
            continue
        else:
            _, artiste['id_genius'] , artiste['url_genius'] = rep_genius
        artiste['id_mb'] = musicbrainz.get_artist_id_by_name(artiste['name'])
        i+=1
        
    """
    Sauvegarde de la base de données JSON.
    """
    print(f"[{this_name}] Écriture dans la base de données... {" "*100}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artistes, f, indent=2, ensure_ascii=False)
    print(f"[{this_name}] Fermeture de la base de données...")


def update_mongo(db_name = "arthur_modal", force_update = False):
    
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
    artistes = []
    client = MongoClient("mongodb://localhost:27017")
    db = client[db_name]
    collection = db["artists"]
    
    """
    Récupération des artistes en ligne depuis Spotify grâce à l'API via spotify.py. Sauvegarde de cette liste dans un autre fichier.
    """
    print(f"[{this_name}] Récupération des artistes en ligne...")
    new_artistes = spotify.get_artists()
    #new_artistes.append({"name": "luther"})
    #new_artistes = [{"name": "luther"}, {"name": "Jul"}, {"name": "Nekfeu"}, {"name": "Alpha Wann"}] 
    '''
    # Sauvegarde de la liste des artistes dans un fichier texte
    '''
    f = open("artists_list.txt", "w", encoding="utf-8")
    for artiste in new_artistes:
        f.write(f"{artiste['name']}\n")
    f.close()
    
    
    longueur = len(new_artistes)
    print(f"[{this_name}] Récupération des artistes en ligne terminée. {longueur} artistes récupérés.")

    """
    Rajout de ces artistes à notre base de données JSON.
    """
    print(f"[{this_name}] Mise à jour de la base de données...")
    i = 0
    for artiste in new_artistes:
        i+=1
        print(f"[{this_name}] [{i}/{longueur}] Mise à jour de l'artiste : {artiste['name']} {" "*100}", end='\r')
        collection.update_one({"name": artiste['name']}, {"$setOnInsert": {"name": artiste['name']}}, upsert=True)
        
    print(f"[{this_name}] Mise à jour de la base de données terminée. {i} artistes mis à jour.") 
    """
    Mise à jour des liens Genius, Last-FM, MusicBrainz... pour chaque artiste.
    """

    fails = []
    print(f"[{this_name}] Mise à jour des liens... {" "*100}")
    length = collection.count_documents({})
    i = 0
    for artiste in collection.find():
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {" "*100}", end='\r')
        
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
        '''
        Mise à jour de l'artiste en entier
        artiste['id_mb'] = musicbrainz.get_artist_id_by_name(artiste['name'])
        '''
        '''
        Mise à jour de l'artiste en partie
        '''
        collection.update_one({"name": artiste['name']}, {"$set": {"id_mb": musicbrainz.get_artist_id_by_name(artiste['name'])}})     
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
                print(f"[{this_name}] Mise à jour de l'artiste : {artist_fail['name']} {" "*100}")
                rep_genius = genius.get_artist_id_by_name_manual()
                if rep_genius is not None:
                    collection.update_one({"name": artist_fail['name']}, {"$set": {"id_genius": rep_genius[1], "url_genius": rep_genius[2]}})
        else:
            print(f"[{this_name}] Pas de mise à jour des fails")
    else:
        print(f"[{this_name}] Pas de fails")
    """
    Sauvegarde de la base de données JSON.
    """
    client.close()
    print(f"[{this_name}] Fermeture de la base de données MongoDB...{' '*100}")
    return fails

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
        print(f"🔍 Traitement de l'artiste : {artist_name} ({i} / {len(all_artists)}) {' '*100}", end='\r')

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
    #update_featurings_and_songs_to_mongo()
    '''
    client = MongoClient("mongodb://localhost:27017")
    db = client["arthur_modal"]
    collection = db["artists"]
    collection.delete_many({})
    '''
    update_mongo()