import requests
import base64
import os
import requests
from tools import get_key
import time
import json

this_name = os.path.basename(__file__)

client_id = get_key("Client_ID_spotify")
client_secret = get_key("Client_secret_spotify")
auth_str = f"{client_id}:{client_secret}"
b64_auth_str = base64.b64encode(auth_str.encode()).decode()

headers = {
    "Authorization": f"Basic {b64_auth_str}"
}

data = {
    "grant_type": "client_credentials"
}

response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
access_token = response.json()['access_token']

headers = {
    "Authorization": f"Bearer {access_token}"
}

params = {
    "q": "genre:\"rap français\"",
    "type": "artist",
    "limit": 50
}

'''
response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
results = response.json()
for artist in results['artists']['items']:
    print(artist['name'], "→", artist['genres'])
'''
def get_popularity(artist_id):
    """
    This function returns the popularity of an artist from Spotify.
    """
    params = {
        "ids": artist_id
    }
    #response = requests.get("https://api.spotify.com/v1/artists", headers=headers, params=params)
    response = requests.get(f"https://api.spotify.com/v1/artists/{artist_id}", headers=headers)
    results = response.json()
    # Vérification de la présence de la clé 'artists' et du contenu
    pop, followers = None, None
    try:
        followers = results['followers']['total']
    except Exception as e:
        followers = None
        print(json.dumps(results, indent=4))
    try:
        pop = results['popularity']
    except Exception as e:
        pop = None
    return pop, followers
    '''
    if 'artists' in results and results['artists']:
        return results['artists'][0]['popularity']
    else:
        print(f"[{this_name}] Erreur : clé 'artists' absente ou vide pour l'id {artist_id}")
        return None
    '''
# Afficher les artistes d'un genre spécifique
def show_artists(genre):
    print(f"[{this_name}] Récupération des artistes de : {genre}")
    i = 0
    for offset in range(0, 1000, 50):
        params["offset"] = offset
        params["q"] = f"genre:\"{genre}\""            
        response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
        artists = response.json()['artists']['items']
        for artist in artists:
            print(f"[{this_name}] [{i}]", artist['name'], artist['id'])
            i += 1

list_genres = ["french rap"] #, "french hip hop", "rap français", "drill français"]    #, "rap", "hip hop", "trap", "pop rap", "r&b", "soul", "new wave rap français"]
def get_artists(genres = list_genres):
    """
    This function returns a list of artists from Spotify.
    """
    artists = []
    for genre in genres:
        print(f"[{this_name}] Récupération des artistes de : {genre}")
        for offset in range(0, 1000, 50):

            #Éviter de spammer l'API
            time.sleep(0.5)

            #Préparation de la requête
            print(f"[{this_name}] Artistes traités : {offset}, récupération des 50 prochains", end='\r')
            params["offset"] = offset
            params["q"] = f"genre:\"{genre}\""            
            response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
            results = response.json()

            empty = True
            for artist in results['artists']['items']:
                empty = False
                artists.append({
                    "name": artist['name'],
                    "id_spotify": artist['id'],
                    "genres": artist['genres']
                })
            if empty:
                break
    print(f"[{this_name}] Récupération terminée{' '*100}")
    return artists

def get_artist_albums(artist_id):
    albums = []
    url = f"https://api.spotify.com/v1/artists/{artist_id}/albums?include_groups=album&limit=50"
    while url:
        response = requests.get(url, headers=headers)
        data = response.json()
        albums += data['items']
        url = data.get('next')  # Pagination
    # Éliminer les doublons (même album réédité dans différents marchés)
    seen = set()
    unique_albums = []
    for album in albums:
        if album['name'] not in seen:
            seen.add(album['name'])
            unique_albums.append(album)
    return unique_albums

# Récupérer les labels de chaque album
def get_album_labels(albums):
    labels = {}
    for album in albums:
        album_id = album['id']
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        response = requests.get(url, headers=headers)
        data = response.json()
        print(json.dumps(response.json(), indent=4))
        labels[data['name']] = data.get('label', 'Inconnu')
    return labels

# Chercher l'ID d'un artiste
def get_artist_id(artist_name):
    url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist"
    response = requests.get(url, headers=headers)
    items = response.json()['artists']['items']
    return items[0]['id'] if items else None

# Fonction principale
def get_artist_album_labels(artist_name):
    artist_id = get_artist_id(artist_name)
    if not artist_id:
        print(f"Artiste introuvable : {artist_name}")
        return {}
    albums = get_artist_albums(artist_id)
    return get_album_labels(albums)

# Exemple d’utilisation
if __name__ == "__main__":
    
    artist_name = "Nekfeu"

    labels = get_artist_album_labels(artist_name)
    for album, label in labels.items():
        print(f"{album} → {label}")

    '''
    artists = get_artists()
    print(f"[{this_name}] {len(artists)} artistes récupérés")
    for artist in artists:
        popularity, followers = get_popularity(artist['id_spotify'])
        print(f"{artist['name']} {artist['id_spotify']} -> Popularity : {popularity} . Followers : {followers}")
        #print(f"[{this_name}] {artist['name']} : {artist['id_spotify']} . Popularity : {get_popularity(artist['id_spotify'])}")
    print(f"[{this_name}] {len(artists)} artistes récupérés")
    
    val = input("Entrez l'id d'un artiste : ")
    print(f"{get_popularity(val)}")
    '''