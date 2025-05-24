from pymongo import MongoClient
import os
from bson.objectid import ObjectId
import networkx as nx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

this_name = os.path.basename(__file__)

def build_graph(clientname, weighted=True, similarity_threshold=0.95, plot_distribution=True):
    print(f"[{this_name}] Building graph...")
    
    # Connexion à la base de données
    client = MongoClient("mongodb://localhost:27017/")
    db = client[clientname]
    artists = db["artists"]

    # Création du graphe
    G = nx.Graph()

    # Récupération des artistes avec embeddings
    artist_list = list(artists.find({"embedding": {"$exists": True}}))
    id_to_embedding = {}
    
    for artist in artist_list:
        print(f"[{this_name}] Adding artist {artist['name']} to graph{' '*100}", end="\r")
        artist_id = artist["id_genius"]
        G.add_node(artist_id,
                   name=str(artist["name"]),
                   id_mongo=str(artist["_id"]),
                   id_genius=int(artist_id),
                   id_spotify=str(artist["id_spotify"]),
                   url_genius=str(artist["url_genius"]),
                   popularity=artist["popularity"],
                   followers=artist["followers"])
        id_to_embedding[artist_id] = np.array(artist["embedding"])

    print(f"\n[{this_name}] All artists added to graph")

    print(f"[{this_name}] Computing cosine similarities and adding edges...")
    artist_ids = list(id_to_embedding.keys())
    embeddings = np.array([id_to_embedding[aid] for aid in artist_ids])

    # Calcul de la matrice de similarité cosinus
    similarity_matrix = cosine_similarity(embeddings)
    all_similarities = []
    for i in range(len(artist_ids)):
        for j in range(i + 1, len(artist_ids)):
            sim = similarity_matrix[i][j]
            score = (sim - similarity_threshold) * 20
            all_similarities.append(score)
            if sim >= similarity_threshold:
                if weighted:
                    G.add_edge(artist_ids[i], artist_ids[j], weight=score)
                else:
                    G.add_edge(artist_ids[i], artist_ids[j])

    print(f"[{this_name}] Graph completed with similarity edges")

    # Tracer la distribution des similarités
    if plot_distribution:
        print(f"[{this_name}] Plotting similarity distribution...")
        plt.figure(figsize=(8, 5))
        plt.hist(all_similarities, bins=50, range=(0, 1), color='steelblue', edgecolor='black')
        plt.title("Distribution des similarités cosinus entre artistes")
        plt.xlabel("Similarité cosinus")
        plt.ylabel("Fréquence")
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        plt.show()

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
    
def delete_small_components(graph, min_size=10):
    """
    Supprime toutes les composantes connexes du graphe ayant moins de min_size nœuds.
    """
    small_components = [c for c in nx.connected_components(graph) if len(c) < min_size]
    nodes_to_remove = set()
    for comp in small_components:
        nodes_to_remove.update(comp)
    graph.remove_nodes_from(nodes_to_remove)
    print(f"[{this_name}] Deleted {len(small_components)} components with less than {min_size} nodes ({len(nodes_to_remove)} nodes removed)")
    return graph

if __name__ == "__main__":
    graph = build_graph("final_db_3", weighted = True)
    #delete_low_degree_nodes(graph, 1, "deleted_nodes_3_2.txt")
    delete_small_components(graph, 5)
    #graph = delete_isolated_nodes(graph)
    # graph_stats(graph)
    nodes_stats(graph)
    
    #Création des différents graphes liés aux différentes méthodes de clustering
    graph = set_clusters(graph, "louvain")
    export_graph_to_gephi(graph, filename = "graph_louvain_last_fm.gexf")
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