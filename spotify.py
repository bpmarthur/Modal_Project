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

# Afficher les artistes d'un genre spécifique
def show_artists_useless(genre):
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
                    "popularity": artist['popularity'],
                    "followers": artist['followers']['total']
                })
            if empty:
                break
    print(f"[{this_name}] Récupération terminée{' '*100}")
    return artists

def show_artists():
    art = get_artists()
    for i in range(len(art)):
        artiste = art[i]
        print(f"[{this_name}] {artiste['name']} : {artiste['id_spotify']} . Popularity : {artiste['popularity']} . Followers : {artiste['followers']}")

def get_artist_data(artist_name):
    """
    Récupère l'id Spotify, la popularité et le nombre de followers d'un artiste à partir de son nom.
    """
    url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist&limit=1"
    response = requests.get(url, headers=headers)
    items = response.json().get('artists', {}).get('items', [])
    if not items:
        return None, None, None
    artist = items[0]
    id_spotify = artist.get('id')
    popularity = artist.get('popularity')
    followers = artist.get('followers', {}).get('total')
    return id_spotify, popularity, followers

# Chercher l'ID d'un artiste
def get_artist_id(artist_name):
    url = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist&limit=1"
    response = requests.get(url, headers=headers)
    items = response.json()['artists']['items']
    return items[0]['id'] if items else None

# Récupérer tous les albums de l’artiste
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
    labels = []
    for album in albums:
        album_id = album['id']
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        response = requests.get(url, headers=headers)
        data = response.json()
        nouveau_label = {}
        nouveau_label['name'] = data['name']
        nouveau_label['data'] = []
        copyrights = data.get('copyrights', [])
        for cr in copyrights:
            if cr['type'] == 'P':
                nouveau_label['data'].append(cr['text'])
        nouveau_label['data'].append(data.get('label', 'Inconnu'))
        labels.append(nouveau_label)
    return labels

# Fonction principale
def get_labels(artist_id):
    albums = get_artist_albums(artist_id)
    return get_album_labels(albums)


if __name__ == "__main__":
    show_artists()

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