from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from tools import get_key
import lyricsgenius # à installer avec pip
import time

GENIUS_API_TOKEN = get_key("Client_access_genius")

genius = lyricsgenius.Genius(GENIUS_API_TOKEN)
genius.timeout = 10
genius.sleep_time = 0.1
genius.skip_non_songs = True
genius.excluded_terms = ["(Remix)", "(Live)"]
genius.remove_section_headers = True

def get_lyrics_from_genius(artist_name, max_songs=5):
    """
    Récupère les paroles des chansons d'un artiste sur Genius.
    
    Args:
        artist_name (str): Nom de l'artiste.
        max_songs (int): Nombre maximum de chansons à récupérer.
    
    Returns:
        List[str]: Liste de paroles (chaque élément est une chanson).
    """
    try:
        artist = genius.search_artist(artist_name, max_songs=max_songs, sort="popularity")
        if artist is None:
            print(f"Aucun résultat pour l'artiste {artist_name}")
            return []

        lyrics_list = []
        for song in artist.songs:
            if song.lyrics:
                lyrics_list.append(song.lyrics)
            time.sleep(0.1)
        return lyrics_list
    except Exception as e:
        print(f"Erreur lors de la récupération de {artist_name} : {e}")
        return []

import re

def clean_lyrics(text, lowercase=True):
    """
    Nettoie un texte de paroles récupéré depuis Genius.
    
    Args:
        text (str): Texte brut récupéré.
        lowercase (bool): Si True, met le texte en minuscules.
    
    Returns:
        str: Texte nettoyé.
    """
    # Supprimer les sections entre crochets (ex: [Refrain], [Couplet 1], [Intro]...)
    text = re.sub(r'\[.*?\]', '', text)
    
    # Supprimer les lignes vides en trop
    text = re.sub(r'\n{2,}', '\n', text)
    
    # Supprimer les métadonnées type "(lyrics)", "(feat...)", etc.
    text = re.sub(r'\(.*?\)', '', text)

    # Supprimer les caractères non pertinents (caractères spéciaux isolés, etc.)
    text = re.sub(r'[^\w\s\'\-.,!?àâäéèêëîïôöùûüç]', '', text)

    # Optionnel : suppression de répétitions trop proches (ad lib ou refrains identiques)
    # → cela peut être pertinent si tu veux éviter les biais de similarité artificielle
    lines = text.strip().split("\n")
    unique_lines = []
    seen = set()
    for line in lines:
        clean_line = line.strip()
        if clean_line and clean_line not in seen:
            unique_lines.append(clean_line)
            seen.add(clean_line)
    text = "\n".join(unique_lines)
    
    # Passage en minuscules si besoin
    if lowercase:
        text = text.lower()
    
    return text.strip()

# embeddings : dict { artist_name: np.array([...]) }
def compute_similarity_matrix(embeddings):
    artists = list(embeddings.keys())
    matrix = cosine_similarity([embeddings[a] for a in artists])
    return artists, matrix
