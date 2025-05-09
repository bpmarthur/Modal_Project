import json
import os
import spotify
import genius
import csv
import time
from pymongo import MongoClient
from bson.objectid import ObjectId

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
    print(f"[{this_name}] Récupération des artistes en ligne...")
    new_artistes = spotify.get_artists()
    f = open("artists_list.txt", "w", encoding="utf-8")
    for artiste in new_artistes:
        f.write(f"{artiste['name']}\n")
    f.close()
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
    print(f"[{this_name}] Mise à jour des liens... {" "*100}")
    length = len(artistes)
    i = 0
    for artiste in artistes:
        print(f"[{this_name}] [{i}/{length}] Mise à jour de : {artiste['name'].strip()} {" "*100}", end='\r')
        _, artiste['id_genius'] , artiste['url_genius'], _= genius.get_artist_id_by_name(artiste['name']+" ")
        #artiste['id_mb']
        #artiste['id_lastfm']

        i+=1
        
    """
    Sauvegarde de la base de données JSON.
    """
    print(f"[{this_name}] Écriture dans la base de données... {" "*100}")
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