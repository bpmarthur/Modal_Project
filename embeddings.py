from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from tools import get_key
import lyricsgenius
import time
import gensim
import re
import genius
import os
import lyricsgenius

this_name = os.path.basename(__file__)

GENIUS_API_TOKEN = get_key("Client_access_genius")

genius_api = lyricsgenius.Genius(GENIUS_API_TOKEN)
genius_api.timeout = 10
genius_api.sleep_time = 0.1
genius_api.skip_non_songs = True
genius_api.excluded_terms = ["(Remix)", "(Live)"]
genius_api.remove_section_headers = True

def get_lyrics_from_genius(artist_name, max_songs=5):
    """
    Récupère les paroles des chansons d'un artiste sur Genius.

    Args:
        artist_name (str): Nom de l'artiste.
        max_songs (int): Nombre maximum de chansons à récupérer.

    Returns:
        List[str]: Liste des paroles de chansons (chaque élément = une chanson).
    """
    try:
        # Recherche de l'artiste sur Genius
        artist = genius_api.search_artist(artist_name, max_songs=max_songs, sort="popularity")
        if artist is None:
            print(f"[{this_name}] Aucun résultat pour l'artiste '{artist_name}'")
            return []

        # Récupération des paroles des chansons
        lyrics_list = []
        for song in artist.songs[:max_songs]:  # on s'assure de ne pas dépasser max_songs
            if song.lyrics:
                lyrics_list.append(song.lyrics.strip())
            time.sleep(0.1)  # pause légère pour éviter le rate limit

        return lyrics_list

    except Exception as e:
        print(f"[{this_name}] Échec pour {artist_name} : {e}")
        return []



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

def vectorize_artist_lyrics(lyrics_dict, model, cleaning_fn=None):
    """
    Convertit les paroles de chaque artiste en un vecteur moyen à l'aide d'un modèle Word2Vec.
    
    Args:
        lyrics_dict (dict): dictionnaire {nom_artiste: texte_paroles}
        model (gensim.models.Word2Vec): modèle pré-entrainé (ex: Word2Bezbar)
        cleaning_fn (function): fonction de nettoyage à appliquer (par défaut : aucun)

    Returns:
        dict: {nom_artiste: vecteur_numpy}
    """
    artist_vectors = {}

    for artist, lyrics in lyrics_dict.items():
        if cleaning_fn:
            lyrics = cleaning_fn(lyrics)

        tokens = lyrics.lower().split()
        valid_tokens = [t for t in tokens if t in model.wv.key_to_index]

        if not valid_tokens:
            print(f"[{this_name}] Aucun mot connu du modèle pour {artist}")
            continue

        # Moyenne des vecteurs
        vectors = np.array([model.wv[t] for t in valid_tokens])
        mean_vector = np.mean(vectors, axis=0)

        artist_vectors[artist] = mean_vector

    return artist_vectors


# embeddings : dict { artist_name: np.array([...]) }
def compute_similarity_matrix(embeddings):
    artists = list(embeddings.keys())
    matrix = cosine_similarity([embeddings[a] for a in artists])
    return artists, matrix


def get_artist_vector(artist_id, model, max_songs=5):
    """
    Pipeline complète pour obtenir le vecteur moyen des paroles d'un artiste.
    
    Args:
        artist_name (str): nom de l'artiste
        model (gensim.models.Word2Vec): modèle Word2Bezbar
        max_songs (int): nombre de chansons à récupérer

    Returns:
        np.ndarray or None: vecteur d'embedding ou None si échec
    """
    artist_name = genius.get_artist_name_by_id(artist_id)
    if artist_name is None:
        return None
    print(f"[{this_name}] Traitement de {artist_name} {' '*100}", end='\r')
    
    # 1. Récupération des paroles
    lyrics_list = get_lyrics_from_genius(artist_name, max_songs=max_songs)
    if lyrics_list == []:
        print(f"[{this_name}] [FAIL] Aucune parole récupérée pour {artist_name}")
        return None
    else: 
        print(f"[{this_name}] ✅✅ {len(lyrics_list)} chansons récupérées pour {artist_name}")

    # 2. Concaténation
    full_text = "\n".join(lyrics_list)

    # 3. Nettoyage
    cleaned = clean_lyrics(full_text)

    # 4. Tokenisation + Vectorisation
    tokens = cleaned.split()
    valid_tokens = [t for t in tokens if t in model.wv.key_to_index]
    
    if not valid_tokens:
        print(f"[{this_name}] Aucun token reconnu pour {artist_name}")
        return None

    vectors = np.array([model.wv[t] for t in valid_tokens])
    return np.mean(vectors, axis=0)

if __name__ == "__main__":
    # Charger le modèle Word2Bezbar
    model = gensim.models.Word2Vec.load("Word2Bezbar-large/word2vec.model")
    
    # Exemple
    artist_name = "Nekfeu"
    artist_id = 13063
    vec = get_artist_vector(artist_id, model)
    
    if vec is not None:
        print(f"Vecteur de {artist_name} :\n{vec[:10]}")  # Affiche les 10 premières dimensions
        print(f"Dimension du vecteur : {vec.shape}")

