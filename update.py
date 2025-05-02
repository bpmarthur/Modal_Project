import json
import os
import spotify
import genius

def update(filename = "artists.txt"):
    """
    This function updates the data in the file.
    """
    
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            artistes = json.load(f)
    else:
        artistes = []

    new_artistes = spotify.get_artists()

    #Rajout des derniers artistes sur Spotify
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
    for artiste in artistes:
        artiste['id_genius'] = genius.get_artist_id_by_name(artiste['name'])

    # Sauvegarde mise à jour du JSON
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(artistes, f, indent=2, ensure_ascii=False)