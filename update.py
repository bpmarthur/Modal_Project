import json
import os
import spotify
import genius

def update(filename = "artists.json"):
    """
    This function updates the data in the file.
    """
    print("Ouverture de la base de données...")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            artistes = json.load(f)
    else:
        artistes = []
    
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
    for artiste in artistes:
        artiste['id_genius'] = genius.get_artist_id_by_name(artiste['name'])
        #artiste['id_mb']
        #artiste['id_lastfm']

    # Sauvegarde mise à jour du JSON
    print("Écriture dans la base de données...")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artistes, f, indent=2, ensure_ascii=False)
    print("Fermeture de la base de données...")

if __name__ == "__main__":
    update()