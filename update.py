import json
import os
import spotify
import genius
import csv
import time
import musicbrainz
from pymongo import MongoClient
from tools import get_key
from bson.objectid import ObjectId

GENIUS_API_TOKEN = get_key("Client_access_genius")

headers = {
    'Authorization': f'Bearer {GENIUS_API_TOKEN}'
}

this_name = os.path.basename(__file__)

def update(filename = "artists.json"):
    
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
    f = open("artists_list.txt", "w", encoding="utf-8")
    for artiste in new_artistes_musicbrainz:
        f.write(f"{artiste['name']}\n")
    f.close()
    print(f"[{this_name}] Récupération des artistes en ligne terminée. {len(new_artistes_musicbrainz)} artistes récupérés via musicbrainz.")
    
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
        else:
            print(f"[{this_name}] Artiste mis à jour : {artiste['name']} {' '*100}", end='\r')
    """
    Mise à jour des liens Genius, Last-FM, MusicBrainz... pour chaque artiste.
    """
    print(f"[{this_name}] Mise à jour des liens... {' '*100}")
    length = len(artistes)
    i = 0
    for artiste in artistes:
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {' '*100}", end='\r')
        object_or_None = genius.get_artist_id_by_name(artiste['name'])
        if object_or_None is None:
            print(f"[{this_name}] Impossible de trouver l'artiste {artiste['name']}")
            continue
        else :
            _, artiste['id_genius'] , artiste['url_genius'], _= object_or_None
        artiste['id_mb'] = musicbrainz.get_artist_id_by_name(artiste['name'])
        #artiste['id_mb']
        #artiste['id_lastfm']

        i+=1
        
    """
    Sauvegarde de la base de données JSON.
    """
    print(f"[{this_name}] Écriture dans la base de données... {' '*100}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artistes, f, indent=2, ensure_ascii=False)
    print(f"[{this_name}] Fermeture de la base de données...")

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

    # Pour faire correspondre un nom à un id dans la base
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

if __name__ == "__main__":
    update()
    #update_json_to_mongo()
    #update_featurings_and_songs_to_mongo()