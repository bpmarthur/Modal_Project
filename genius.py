import requests
import time
import os
import json
from tools import get_key

GENIUS_API_TOKEN = get_key("Client_access_genius")

headers = {
    'Authorization': f'Bearer {GENIUS_API_TOKEN}'
}

this_name = os.path.basename(__file__)

def get_song_id_by_name(song_name):
    base_url = 'https://api.genius.com/search'
    params = {'q': song_name}
    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json()['response']['hits']
        return results[0]['result']['id']
    else:
        print(f"[{this_name}] Erreur dans la requête :", response.status_code)
        
def search_song(query):
    base_url = 'https://api.genius.com/search'
    params = {'q': query}
    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json()['response']['hits']
        for hit in results:
            song = hit['result']
            print(f"{song['full_title']} -> {song['url']}")
    else:
        print(f"[{this_name}] Erreur dans la requête :", response.status_code)

def get_all_songs_from_artist(artist_id, max_songs=1000):
    base_url = f"https://api.genius.com/artists/{artist_id}/songs"
    songs = []
    page = 1

    while True:
        params = {
            "per_page": 50,
            "page": page,
            "sort": "popularity"
        }
        response = requests.get(base_url, headers=headers, params=params)
        data = response.json()
        new_songs = data["response"]["songs"]

        if not new_songs:
            break

        songs.extend(new_songs)

        print(f"[{this_name}] Page {page} : {len(new_songs)} chansons récupérées")
        page += 1
        time.sleep(0.2)  # pour éviter d'être bloqué par l'API

        if len(songs) >= max_songs:
            break

    return songs

def get_artist_url_by_id(artist_id):
    url = f"https://api.genius.com/artists/{artist_id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[{this_name}] Erreur :", response.status_code)
        return None

    data = response.json()
    artist_url = data["response"]["artist"]["url"]
    return artist_url

def get_artist_id_by_name(artist_name, artist_data = ""):
    url = "https://api.genius.com/search"
    if artist_data == "":
        params = {"q": artist_name}
    else:
        params = {"q": f"{artist_name} {' '.join(artist_data)}"}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print(f"[{this_name}] Erreur :", response.status_code)
        return None

    hits = response.json()["response"]["hits"]
    if not hits:
        print(f"[{this_name}] Aucun résultat trouvé.")
        return None

    # On prend un artiste qui matche avec le nom
    artist = hits[0]["result"]["primary_artist"]
    found = False
    index_rep = 0
    for i in range(0, len(hits)):
        if hits[i]["result"]["primary_artist"]["name"].lower() == artist_name.lower().strip():
            artist = hits[i]["result"]["primary_artist"]
            #print(f"[{this_name}] [{i}] Nom : {artist['name']}, ID : {artist['id']}, URL : {artist['url']}")   #Debug
            found = True
            index_rep = i
            break
    if not found:
        print(f"[{this_name}] Aucun artiste trouvé pour {artist_name}")
        #print(f"[{this_name}] [0] Nom : {artist['name']}, ID : {artist['id']}, URL : {artist['url']}") #Debug
    
    '''
    # On récupère l'url de l'artiste
    response = requests.get(f"https://api.genius.com/artists/{artist["id"]}", headers=headers)
    data = response.json()

    url = data["response"]["artist"]["url"]
    '''
    url = artist["url"]
    id = artist["id"]
    name = artist["name"]

    return name, id, url, index_rep #Retourne le nom, l'id, l'url de l'artiste et l'index de la réponse

def get_artists_from_song(song_id):
    url = f"https://api.genius.com/songs/{song_id}"
    response = requests.get(url, headers=headers)
    print(response)
    if response.status_code != 200:
        print("Erreur :", response.status_code)
        return

    song = response.json()["response"]["song"]
    main_artist = song["primary_artist"]["name"]
    featured_artists = [a["name"] for a in song["featured_artists"]]

    print(f"[{this_name}] Artiste principal :", main_artist)
    if featured_artists:
        print("Featuring :", ", ".join(featured_artists))
    else:
        print("Pas de featuring.")
    
    return {
        "primary": main_artist,
        "featurings": featured_artists
    }

def get_song_from_id(id):
    url = f"https://api.genius.com/songs/{id}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[{this_name}] Erreur :", response.status_code)
        return None

    song = response.json()["response"]["song"]
    #print(json.dumps(song, indent=2, ensure_ascii=False))
    with open("resultat.json", "w", encoding="utf-8") as f:
        json.dump(song, f, indent=2, ensure_ascii=False)
    return {
        "title": song["title"],
        "url": song["url"],
        "primary_artist": song["primary_artist"]["name"],
        "featured_artists": [a["name"] for a in song["featured_artists"]]
    }
def show_artist():
    artist_name = input(f"[{this_name}] Nom de l'artiste : ")
    #data = input("Data : ")
    name, id, url, index = get_artist_id_by_name(artist_name)
    print(f"[{this_name}] [{index}] Nom : {name}, ID : {id}, URL : {url}")

if __name__ == "__main__":
    show_artist()
    # Exemple
    #search_song("Lose Yourself Eminem")

    # Exemple : Eminem (ID = 45)
    #songs = get_all_songs_from_artist(artist_id=45,max_songs=10)
    #songs = get_all_songs_from_artist(artist_id=get_artist_id_by_name("lutherantz"),max_songs=1000)

    # Affiche les titres et URLs
    #for song in songs:
    #    print(f"{song['title']} -> {song['url']}")

    #artists = get_artists_from_song(get_song_id_by_name("Lose Yourself Eminem"))
    #print(artists)

    #get_song_from_id(get_song_id_by_name("Lose Yourself Eminem"))

    #print(json.dumps(data, indent=2, ensure_ascii=False))