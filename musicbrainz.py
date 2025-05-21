# musicbrainz.py
import musicbrainzngs
import unicodedata    
import requests
import time
import string

musicbrainzngs.set_useragent("musicbrainzngs","0.7.0")

HEADERS = {
    "User-Agent": "RapCollabParser/1.0 ( contact@example.org )"
}

BASE_URL_MB = "https://musicbrainz.org/ws/2"

def normalize_string(s):
    # Supprime les accents, met en minuscules et enlève les caractères non alphanumériques
    s = s.lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')  # enlève les diacritiques
    return s

# def complete_artist_list(genre = ["rap français"]):
    

def get_artist_id_by_name(name):
    try:
        result = musicbrainzngs.search_artists(artist=name, limit=1)
        if result['artist-count'] > 0:
            return result['artist-list'][0]['id']
        else:
            return None
    except Exception as e:
        print(f"Erreur MusicBrainz pour {name} : {e}")
        return None

def get_artists():
    all_artists = []

    for letter in string.ascii_lowercase:
        query = f'artist:{letter}* AND (tag:"rap" OR tag:"hip hop" OR tag:"trap" OR "cloud rap" ) AND (country:FR OR country:BE)'
        params = {
            "query": query,
            "fmt": "json",
            "limit": 100
        }

        response = requests.get(f"{BASE_URL_MB}/artist", params=params, headers=HEADERS)
        time.sleep(0.2)
        response.raise_for_status()
        results = response.json().get("artists", [])
        
        for i, artist in enumerate(results):
            name = artist.get("name")
            if name:
                all_artists.append({
                    "name": artist['name'],
                    "id_spotify": artist.get('id')
                })
                print(f" [musicbrainz.py] {i} / {len(results)} artistes récupérés pour la lettre '{letter.upper()}*' {100 * ' '}", end = "\r")

    return all_artists

    
if __name__ == "__main__":
    # Exemple d'utilisation
    artist_name = "The Beatles"
    artist_id = get_artist_id_by_name(artist_name)
    if artist_id:
        print(f"L'ID MusicBrainz de {artist_name} est : {artist_id}")
    else:
        print(f"Aucun ID trouvé pour {artist_name}")
