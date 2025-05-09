import json
import os
import spotify
import genius
import musicbrainz
from pymongo import MongoClient
from tools import get_key

GENIUS_API_TOKEN = get_key("Client_access_genius")

headers = {
    'Authorization': f'Bearer {GENIUS_API_TOKEN}'
}

def update(filename = "artists.json"):
    """
    This function updates the data in the file.
    """
    print("Ouverture de la base de données...")
    artistes = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                artistes = json.load(f)
            except json.JSONDecodeError:
                print("⚠️ Erreur : le fichier JSON est mal formé.")
    
    print("Récupération des artistes en ligne...")

    new_artistes = spotify.get_artists()

    #Rajout des derniers artistes sur Spotify
    print("Mise à jour de notre liste...")
    for artiste in new_artistes:
        if not any(a['name'] == artiste['name'] for a in artistes):
            # Ajouter l'artiste à la liste
            artistes.append(artiste)
            print(f"Ajout de l'artiste : {artiste['name']} {' ' * 100}", end='\r')
        else:
            print(f"Artiste mis à jour : {artiste['name']} {' ' * 100}", end='\r')
            '''
            # Mettre à jour les genres de l'artiste
            for a in artistes:
                if a['name'] == artiste['name']:
                    a['genres'] = list(set(a['genres'] + artiste['genres']))
                    print(f"Artiste mis à jour : {artiste['name']}")
            '''
    #Mise à jour de tous les liens
    print(f"Mise à jour des liens... {' '*100}")
    length = len(artistes)
    i = 0
    for artiste in artistes:
        print(f"[{i}/{length}] Mise à jour de : {artiste['name']} {' '*100}", end='\r')
        artiste['id_genius'] , artiste['url_genius']= genius.get_artist_id_by_name(artiste['name'])
        artiste['id_mb'] = musicbrainz.get_artist_id_by_name(artiste['name'])
        #artiste['id_lastfm']

        i+=1
    # Sauvegarde mise à jour du JSON
    print(f"Écriture dans la base de données... {' '*100}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artistes, f, indent=2, ensure_ascii=False)
    print("Fermeture de la base de données...")

def update_json_to_mongo(filename = "artists.json"):
    """
    This function updates the data in the MongoDB database.
    """
    pass
    print("Ouverture de la base de données...")
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

    

if __name__ == "__main__":
    update_featurings_and_songs_to_mongo()