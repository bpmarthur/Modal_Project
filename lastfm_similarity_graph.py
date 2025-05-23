import requests
import networkx as nx
from pymongo import MongoClient
import time
import tools

API_KEY = tools.get_key("LASTFM_API_KEY")
BASE_URL = "http://ws.audioscrobbler.com/2.0/"

client = MongoClient("mongodb://localhost:27017/")
db = client["musicdb"]
artists_col = db["artists"]

# Liste des artistes
all_artists = list(artists_col.find({}))
artist_names = [artist["name"] for artist in all_artists]
artist_set = set(name.lower() for name in artist_names)  # Pour comparaison rapide

# Création du graphe
G = nx.Graph()

# Ajout des noeuds
for artist in artist_names:
    G.add_node(artist)

# Recherche des similarités
for i, artist in enumerate(artist_names):
    print(f"Traitement de l'artiste : {artist} ({i}/{len(artist_names)}) {' ' * 100}", end="\r")
    params = {
        "method": "artist.getsimilar",
        "artist": artist,
        "api_key": API_KEY,
        "format": "json",
        "limit": 50
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        similars = data.get("similarartists", {}).get("artist", [])

        for sim_artist in similars:
            name = sim_artist["name"]
            score = float(sim_artist["match"])

            if name.lower() in artist_set:
                # Pour éviter les doublons d’arêtes
                if G.has_edge(artist, name):
                    existing_weight = G[artist][name]['weight']
                    G[artist][name]['weight'] = max(existing_weight, score)  # ou moyenne, etc.
                else:
                    G.add_edge(artist, name, weight=score)

    except Exception as e:
        print(f"Erreur avec {artist} : {e}")
    
    time.sleep(0.2)  # Pour respecter le quota API (5 req/sec max)

print(f"Graphe construit avec {len(G.nodes)} nœuds et {len(G.edges)} arêtes.")
