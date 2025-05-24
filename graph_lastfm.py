from pymongo import MongoClient
import os
import requests
import networkx as nx
import time
from dotenv import load_dotenv

this_name = os.path.basename(__file__)

# Chargement de la clé API
load_dotenv("API.md")
API_KEY = os.getenv("LASTFM_API_KEY")
BASE_URL_LFM = "http://ws.audioscrobbler.com/2.0/"

def get_similar_artists_lastfm(artist_name, limit=20):
    params = {
        "method": "artist.getsimilar",
        "artist": artist_name,
        "api_key": API_KEY,
        "format": "json",
        "limit": limit
    }
    response = requests.get(BASE_URL_LFM, params=params)
    response.raise_for_status()
    return response.json()

def build_graph(db_name, limit=20):
    client = MongoClient("mongodb://localhost:27017/")
    db = client[db_name]
    artists_collection = db["artists"]

    G = nx.Graph()
    added_edges = set()

    all_artists = list(artists_collection.find({}))
    name_to_artist = {}

    for artist in all_artists:
        name = artist["name"]
        id_genius = artist["id_genius"]

        G.add_node(id_genius, **{
            "name": name,
            "id_mongo": str(artist["_id"]),
            "id_genius": id_genius,
            "id_spotify": str(artist["id_spotify"]),
            "url_genius": str(artist["url_genius"]),
            "popularity": artist.get("popularity"),
            "followers": artist.get("followers")
        })
        name_to_artist[name.lower()] = artist  # pour correspondance par nom, insensible à la casse
        
    i = 0
    nb_aretes_current = 0
    for artist in all_artists:
        
        id_genius = artist["id_genius"]

        try:
            response = get_similar_artists_lastfm(artist["name"], limit=limit)
            similar = response["similarartists"]["artist"]
        except Exception as e:
            print(f"Erreur pour {artist['name']} : {e}")
            continue

        for sim_artist in similar:
            sim_name = sim_artist["name"].strip()
            sim_score = float(sim_artist["match"])

            # Vérifie que l'artiste similaire est dans la base MongoDB
            if sim_name and sim_name.lower() in name_to_artist:
                target_artist = name_to_artist[sim_name.lower()]
                target_id = target_artist["id_genius"]
                edge_key = tuple(sorted((id_genius, target_id)))
                if edge_key not in added_edges:
                    G.add_edge(id_genius, target_id, weight=sim_score)
                    added_edges.add(edge_key)

        time.sleep(0.1)  # Respecte les limites d’API
        print(f"[{this_name}] Ajout de {artist['name']} ({i+1}/{len(G.nodes)}) : {len(G.edges) - nb_aretes_current} nouvelles arêtes.{' '*100}", end="\r")
        nb_aretes_current = len(G.edges)
        i += 1
    print(f" [{this_name}] Graphe construit avec {len(G.nodes)} noeuds et {len(G.edges)} arêtes.")
    return G


        
def louvain(graph):
    return nx.community.louvain_communities(graph, seed=123)

def clique_percolation(graph, k:int):
    return nx.community.k_clique_communities(graph, k)

def label_propagation(graph):
    return nx.community.label_propagation_communities(graph)

def girvan_newman(graph):
    return nx.community.girvan_newman(graph)

def k_clique(graph, k:int):
    return nx.community.k_clique_communities(graph, k)

def greedy_modularity(graph):
    return nx.community.greedy_modularity_communities(graph)

def graph_stats(graph):
    print(f"[{this_name}] Graph stats:")
    print(f"Number of nodes: {graph.number_of_nodes()}")
    print(f"Number of edges: {graph.number_of_edges()}")
    print(f"Average degree: {sum(dict(graph.degree()).values()) / graph.number_of_nodes():.2f}")
    print(f"Density: {nx.density(graph):.4f}")
    print(f"Clustering coefficient: {nx.average_clustering(graph):.4f}")
    print(f"Diameter: {nx.diameter(graph)}")
    print(f"Average shortest path length: {nx.average_shortest_path_length(graph):.2f}")
    print(f"Connected components: {nx.number_connected_components(graph)}")
    print(f"Is connected: {nx.is_connected(graph)}")
    print(f"Average clustering coefficient: {nx.average_clustering(graph):.4f}")

    print(f"[{this_name}] ----------------------------------------------------")

def cluster_stats(graph, clusters):
    print(f"[{this_name}] Cluster stats:")
    print(f"Number of communities: {len(set(nx.get_node_attributes(graph, 'cluster').values()))}")
    print(f"Number of nodes in each community: {len(dict(nx.get_node_attributes(graph, 'cluster')))}")
    print(f"Number of edges in each community: {len(dict(nx.get_edge_attributes(graph, 'weight')))}")
    #mod = nx.algorithms.community.quality.modularity(graph, clusters)
    #print(f"Modularity: {mod:.4f}")
    #print(f"Modularity: {nx.algorithms.community.modularity(graph, nx.get_node_attributes(graph, 'cluster').values())}")
    print(f"[{this_name}] ----------------------------------------------------")

def nodes_stats(graph):
    print(f"[{this_name}] Nodes stats:")
    centrality = nx.degree_centrality(graph)
    top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]  # Top 10
    print("Top nodes by degree centrality:", [graph.nodes[x[0]]["name"] for x in top_nodes])
    print(f"[{this_name}] ----------------------------------------------------")

def delete_isolated_nodes(graph):
    print(f"[{this_name}] Deleting isolated nodes...")
    isolated_nodes = list(nx.isolates(graph))
    graph.remove_nodes_from(isolated_nodes)
    print(f"[{this_name}] Deleted {len(isolated_nodes)} isolated nodes")
    return graph

def set_clusters(graph, method, k:int = 3):
    print(f"[{this_name}] Setting clusters using {method}...")
    clusters = []
    if method == "louvain":
        clusters = louvain(graph)
    elif method == "clique_percolation":
        clusters = clique_percolation(graph, k)
    elif method == "label_propagation":
        clusters = label_propagation(graph)
    elif method == "girvan_newman":
        clusters = girvan_newman(graph)
    elif method == "k_clique":
        clusters = k_clique(graph, k)
    elif method == "greedy_modularity":
        clusters = greedy_modularity(graph)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    for i, cluster in enumerate(clusters):
        for node in cluster:
            graph.nodes[node]["cluster"] = i
    
    cluster_stats(graph, clusters)
    return graph

def export_graph_to_gephi(graph, filename = "graph.gexf"):
    rel_path = "./graphs/"
    file_path = rel_path+filename
    print(f"[{this_name}] Exporting graph to Gephi...")
    os.makedirs("./graphs", exist_ok=True)
    nx.write_gexf(graph, file_path)
    print(f"[{this_name}] Graph exported to {file_path}")

if __name__ == "__main__":
    graph = build_graph("data_final")
    # graph = delete_isolated_nodes(graph)
    # graph_stats(graph)
    # nodes_stats(graph)
    
    #Création des différents graphes liés aux différentes méthodes de clustering
    # graph = set_clusters(graph, "louvain")
    # export_graph_to_gephi(graph, filename = "graph_louvain.gexf")
    '''
    graph = set_clusters(graph, "clique_percolation", 5)
    export_graph_to_gephi(graph, "graph_clique_percolation.gexf")

    
    graph = set_clusters(graph, "label_propagation")
    export_graph_to_gephi(graph, "graph_label_propagation.gexf")
    graph = set_clusters(graph, "girvan_newman")
    export_graph_to_gephi(graph, "graph_girvan_newman.gexf")
    graph = set_clusters(graph, "k_clique", 3)
    export_graph_to_gephi(graph, "graph_k_clique.gexf")
    graph = set_clusters(graph, "greedy_modularity")
    export_graph_to_gephi(graph, "graph_greedy_modularity.gexf")
    '''