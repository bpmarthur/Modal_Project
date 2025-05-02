import json
import os
import spotify
import genius

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
            print(f"Ajout de l'artiste : {artiste['name']}")
        else:
            print(f"Artiste mis à jour : {artiste['name']}")
            '''
            # Mettre à jour les genres de l'artiste
            for a in artistes:
                if a['name'] == artiste['name']:
                    a['genres'] = list(set(a['genres'] + artiste['genres']))
                    print(f"Artiste mis à jour : {artiste['name']}")
            '''
    #Mise à jour de tous les liens
    print("Mise à jour des liens...")
    length = len(artistes)
    i = 0
    for artiste in artistes:
        print(f"[i/{length}] Mise à jour de : {artiste['name']} + {" "*100}", end='\r')
        artiste['id_genius'] = genius.get_artist_id_by_name(artiste['name'])
        #artiste['id_mb']
        #artiste['id_lastfm']

        i+=1
    # Sauvegarde mise à jour du JSON
    print(f"Écriture dans la base de données... {""*100}", end='\r')
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artistes, f, indent=2, ensure_ascii=False)
    print("Fermeture de la base de données...")

if __name__ == "__main__":
    update()