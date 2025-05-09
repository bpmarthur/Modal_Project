import requests
import time
import json
from tools import get_key

GENIUS_API_TOKEN = get_key("Client_access_genius")

headers = {
    'Authorization': f'Bearer {GENIUS_API_TOKEN}'
}

def get_song_id_by_name(song_name):
    base_url = 'https://api.genius.com/search'
    params = {'q': song_name}
    response = requests.get(base_url, headers=headers, params=params)

    if response.status_code == 200:
        results = response.json()['response']['hits']
        return results[0]['result']['id']
    else:
        print("Erreur dans la requête :", response.status_code)
        
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
        print("Erreur dans la requête :", response.status_code)

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

        print(f"Page {page} : {len(new_songs)} chansons récupérées")
        page += 1
        time.sleep(0.2)  # pour éviter d'être bloqué par l'API

        if len(songs) >= max_songs:
            break

    return songs


def get_artist_id_by_name(artist_name):
    url = "https://api.genius.com/search"
    params = {"q": artist_name}
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        print("Erreur :", response.status_code)
        return None

    hits = response.json()["response"]["hits"]
    if not hits:
        print("Aucun résultat trouvé.")
        return None

    # On prend l'artiste principal du premier résultat
    artist = hits[0]["result"]["primary_artist"]
    #print(f"Nom : {artist['name']}, ID : {artist['id']}")

    response = requests.get(f"https://api.genius.com/artists/{artist['id']}", headers=headers)
    data = response.json()

    url = data["response"]["artist"]["url"]
    return artist["id"], url

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

    print("Artiste principal :", main_artist)
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
        print("Erreur :", response.status_code)
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
    
def get_artist_featurings(artist_id, max_pages=1):
    
    songs = []
    for page in range(1, max_pages + 1):
        url = f'https://api.genius.com/artists/{artist_id}/songs'
        params = {
            'page': page,
            'sort': 'popularity'
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Erreur page {page} : {response.status_code}")
            break

        data = response.json()
        song_list = data.get('response', {}).get('songs', [])

        for i, song in enumerate(song_list):
            title = song.get('title')
            song_id = song.get('id')
            primary_artist = song.get('primary_artist', {}).get('name')
            featured_artists = song.get('featured_artists', [])
            print(f"Traitement de la page {page} / ? ... {' '*100}", end='\r')

            # Extraire les noms des artistes (principal + feats)
            authors = [primary_artist] + [artist['name'] for artist in featured_artists]
            if len(authors) > 1:
                songs.append((song_id, title, authors))

        if not song_list:
            break

    return songs


if __name__ == "__main__":
    pass
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