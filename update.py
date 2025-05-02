import json
import os
import spotify
import genius
from pymongo import MongoClient

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
            print(f"Ajout de l'artiste : {artiste['name']} {" "*100}", end='\r')
        else:
            print(f"Artiste mis à jour : {artiste['name']} {" "*100}", end='\r')
            '''
            # Mettre à jour les genres de l'artiste
            for a in artistes:
                if a['name'] == artiste['name']:
                    a['genres'] = list(set(a['genres'] + artiste['genres']))
                    print(f"Artiste mis à jour : {artiste['name']}")
            '''
    #Mise à jour de tous les liens
    print(f"Mise à jour des liens... {" "*100}")
    length = len(artistes)
    i = 0
    for artiste in artistes:
        print(f"[{i}/{length}] Mise à jour de : {artiste['name']} {" "*100}", end='\r')
        artiste['id_genius'] , artiste['url_genius']= genius.get_artist_id_by_name(artiste['name'])
        #artiste['id_mb']
        #artiste['id_lastfm']

        i+=1
    # Sauvegarde mise à jour du JSON
    print(f"Écriture dans la base de données... {""*100}")
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

if __name__ == "__main__":
    update_json_to_mongo()