import requests
import time
import os
import json
from tools import get_key
import sys
import math

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
        time.sleep(0.05)  # pour éviter d'être bloqué par l'API

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

def get_artist_id_by_name_manual():  
    found = False
    artist = None
    while not found:
        requete = input(f"[{this_name}] (entrez 0 si vous voulez quitter) Requête : ")
        if requete == "0":
            return None  
        url = "https://api.genius.com/search"
        params = {"q": requete}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"[{this_name}] Erreur :", response.status_code)
            return None
        
        hits = response.json()["response"]["hits"]
        if not hits:
            print(f"[{this_name}] Aucun résultat trouvé.")
            return None

        #On liste les artistes
        pair = True
        for i in range(0, len(hits)):
            print(f"[{i}] Nom : {hits[i]['result']['primary_artist']['name']}, ID : {hits[i]['result']['primary_artist']['id']}, URL : {hits[i]['result']['primary_artist']['url']}", end = " ")   #Debug
            if pair:
                print('\t', end = " ")
            else:
                print('\n', end = "")
            pair = not pair
        if not pair:
            print('\n', end = "")
        rep = ""
        while True:
            rep = input(f"Choisissez l'artiste qui convient, sinon entrez n'importe quel chiffre : ")
            try:
                rep = int(rep)
                break  # Si ça marche, on sort de la boucle
            except ValueError:
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[K")
                print("Ce n'est pas un entier valide. Réessayez.", end=' ')
        #Supprimer les lignes d'avant
        sys.stdout.write("\033[K")

        for i in range(0, math.ceil(len(hits)/2)+2):
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
        '''
        sys.stdout.write("\033[F")
        time.sleep(0.1)
        sys.stdout.write("\033[K")
        time.sleep(1)    
        '''

        if rep >= 0 and rep < len(hits):
            artist = hits[rep]["result"]["primary_artist"]
            found = True
            break
        else:
            print(f"[{this_name}] Aucun résultat sélectionné.")
    print(f"[{this_name}] Artiste Sélectionné  [{rep}] Nom : {artist['name']}, ID : {artist['id']}, URL : {artist['url']}")   #Debug
    url = artist["url"]
    id = artist["id"]
    name = artist["name"]

    return name, id, url     #Retourne le nom, l'id, l'url de l'artiste et l'index de la réponse

specifications = ["fr"] #, "fra", "rap fr", "rap français", "french rap", "new wave"] 
def get_artist_id_by_name(artist_name, artist_data = None):    
    url = "https://api.genius.com/search"
    if artist_data is None:
        params = {"q": artist_name}
    else:
        print(f"[{this_name}] Recherche de {artist_name} avec la spécification {artist_data} -> ", end='')
        params = {"q": f"{artist_name} {' '.join(artist_data)}"}
    response = requests.get(url, headers=headers, params=params)
    
    #print(json.dumps(response.json(), indent=2))   #Debug, affichage de la requête
    
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
    for i in range(0, len(hits)):
        #print(f"[{this_name}] [{i}] Nom : {hits[i]['result']['primary_artist']['name']}, ID : {hits[i]['result']['primary_artist']['id']}, URL : {hits[i]['result']['primary_artist']['url']}")   #Debug
        nom_genius = hits[i]["result"]["primary_artist"]["name"]
        nom_genius_clean = ''.join('\'' if letter == '’' else letter for letter in nom_genius)
        if nom_genius_clean.lower() == artist_name.lower().strip():
            artist = hits[i]["result"]["primary_artist"]
            #print(f"[{this_name}] [{i}] Nom : {artist['name']}, ID : {artist['id']}, URL : {artist['url']}")   #Debug
            found = True
            break

    if not found and artist_data is None:
        for spec in specifications:
            retour = get_artist_id_by_name(artist_name, artist_data = spec)
            if retour is not None:
                return retour
        return None
        #print(f"[{this_name}] [0] Nom : {artist['name']}, ID : {artist['id']}, URL : {artist['url']}") #Debug
    elif not found:
        print(f"aucun artiste trouvé.")
        return None
    elif found and artist_data is not None:
        print(f"artiste trouvé.")

    '''
    # On récupère l'url de l'artiste
    response = requests.get(f"https://api.genius.com/artists/{artist["id"]}", headers=headers)
    data = response.json()

    url = data["response"]["artist"]["url"]
    '''
    url = artist["url"]
    id = artist["id"]
    name = artist["name"]

    return name, id, url #Retourne le nom, l'id, l'url de l'artiste et l'index de la réponse

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
    reponse = get_artist_id_by_name(artist_name)
    if reponse is None:
        print(f"[{this_name}] Résultat -> Rien trouvé")
        return
    name, id, url = reponse
    print(f"[{this_name}] Résultat -> Nom : {name}, ID : {id}, URL : {url}")
    

def show_artist_manual():
    reponse = get_artist_id_by_name_manual()
    if reponse is None:
        print(f"[{this_name}] Aucune réponse trouvée")
        return
    
def get_artist_name_by_id(id):
    url = f"https://api.genius.com/artists/{id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[{this_name}] Erreur :", response.status_code)
        return None
    data = response.json()
    artist_name = data["response"]["artist"]["name"]
    return artist_name
    
def get_artist_name_by_id(id):
    url = f"https://api.genius.com/artists/{id}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[{this_name}] Erreur :", response.status_code)
        return None
    data = response.json()
    artist_name = data["response"]["artist"]["name"]
    return artist_name
    
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
            break   #Pas continue ?

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
    show_artist_manual()
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