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

def get_monthly_listeners(artist_name):
    """
    This function returns the monthly listeners of an artist from Spotify.
    """
    params = {
        "q": f"artist:{artist_name}",
        "type": "artist",
        "limit": 1
    }
    response = requests.get("https://api.spotify.com/v1/search", headers=headers, params=params)
    results = response.json()
    time.sleep(0.1)
    if results['artists']['items']:
        return results['artists']['items'][0]['followers']['total']
    else:
        return None
    


if __name__ == "__main__":
    '''
    artists = get_artists()
    print(f"[{this_name}] {len(artists)} artistes récupérés")
    for artist in artists:
        popularity, followers = get_popularity(artist['id_spotify'])
        print(f"{artist['name']} {artist['id_spotify']} -> Popularity : {popularity} . Followers : {followers}")
        #print(f"[{this_name}] {artist['name']} : {artist['id_spotify']} . Popularity : {get_popularity(artist['id_spotify'])}")
    print(f"[{this_name}] {len(artists)} artistes récupérés")
    '''
    # val = input("Entrez l'id d'un artiste : ")
    # print(f"{get_popularity(val)}")
    def load_artists_from_file(file_path="artists_list.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    artists = load_artists_from_file()
    for artist in artists:
        try:
            listeners = get_monthly_listeners(artist)
            if listeners is None or listeners <= 10000:
                print(f"{artist} → {listeners if listeners else 'introuvable'} auditeurs mensuels")
        except Exception as e:
            print(f"❌ Erreur avec {artist} : {e}")
