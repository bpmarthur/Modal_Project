# musicbrainz.py
import musicbrainzngs
import unicodedata

musicbrainzngs.set_useragent("musicbrainzngs","0.7.0")

def normalize_string(s):
    # Supprime les accents, met en minuscules et enlève les caractères non alphanumériques
    s = s.lower()
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')  # enlève les diacritiques
    return s

def complete_artist_list(genre = ["rap français"]):
    

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
    
if __name__ == "__main__":
    # Exemple d'utilisation
    artist_name = "The Beatles"
    artist_id = get_artist_id_by_name(artist_name)
    if artist_id:
        print(f"L'ID MusicBrainz de {artist_name} est : {artist_id}")
    else:
        print(f"Aucun ID trouvé pour {artist_name}")
