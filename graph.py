from pymongo import MongoClient
import os
from bson.objectid import ObjectId
import networkx as nx
from itertools import combinations
import matplotlib.pyplot as plt


this_name = os.path.basename(__file__)

def build_graph(clientname, weighted = True):
    print(f"[{this_name}] Building graph...")
    #Récupération des données
    client = MongoClient("mongodb://localhost:27017/")
    db = client[clientname]  # nom de la base de données
    artists = db["artists"] 
    featurings = db["featurings"] 

    #Création du graphe
    G = nx.Graph()

    #On itère sur les artistes
    for artist in artists.find({}):
        print(f"[{this_name}] Adding artist {artist['name']} to graph{' '*100}", end ="\r")
        G.add_node(artist["id_genius"], name=str(artist["name"]), id_mongo=str(artist["_id"]), id_genius= int(artist["id_genius"]), pop = int(artist['popularity']), followers = int(artist["followers"]), id_mb = str(artist["id_mb"]), id_spotify=str(artist["id_spotify"]),url_genius = str(artist["url_genius"]))

    print(f"[{this_name}] All artists added to graph")
    i = 0
    #On itère sur les featurings de la chanson
    print(f"[{this_name}] Adding featurings to graph {len(list(featurings.find({})))} featurings found")
    for featuring in featurings.find({}):
        pairs = list(combinations(featuring['artists_genius_id'], 2))   #S'il n'y a qu'un seul artiste, on ne peut pas faire de featuring
        
        for pair in pairs:
            id_1, id_2 = pair
            #print(f"pair : {pair}")
            node_1 = artists.find_one({"id_genius": id_1})
            node_2 = artists.find_one({"id_genius": id_2})
            #print(f"\033[F[{this_name}] Adding featuring {featuring['title']} {node_1['name']} {node_2['name']} to graph{' '*100}", end ='')
            if G.has_edge(id_1, id_2):
                if weighted:
                    G[id_1][id_2]["weight"] += 1
                    i += 1
            else:
                G.add_edge(id_1, id_2, weight=1)
                i += 1
    print(f"[{this_name}] All featurings added to graph. Number of edges added: {i}")
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
    #print(f"Diameter: {nx.diameter(graph)}")
    #print(f"Average shortest path length: {nx.average_shortest_path_length(graph):.2f}")
    print(f"Connected components: {nx.number_connected_components(graph)}")
    print(f"Is connected: {nx.is_connected(graph)}")
    print(f"Average clustering coefficient: {nx.average_clustering(graph):.4f}")

    print(f"[{this_name}] ----------------------------------------------------")

def cluster_stats(graph, clusters):
    print(f"[{this_name}] Cluster stats:")
    print(f"Number of communities: {len(set(nx.get_node_attributes(graph, 'cluster').values()))}")
    print(f"Number of nodes in each community:")
    for i, cluster in enumerate(clusters):
        print(f"  Community {i}: {len(cluster)} nodes")
    #print(f"Number of edges in each community: {len(dict(nx.get_edge_attributes(graph, 'weight')))}")
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

def delete_low_degree_nodes(graph, k, filename=None):
    """
    Supprime tous les noeuds du graphe dont le degré est strictement inférieur à k.
    Si filename est fourni, enregistre les noms des noeuds supprimés dans ce fichier.
    """
    low_degree_nodes = [node for node, degree in dict(graph.degree()).items() if degree < k]
    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            for node in low_degree_nodes:
                name = graph.nodes[node].get("name", str(node))
                f.write(name + "\n")
    graph.remove_nodes_from(low_degree_nodes)
    print(f"[{this_name}] Deleted {len(low_degree_nodes)} nodes with degree < {k}")
    return graph

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
    graph = build_graph("final_db_3", weighted = True)

    # Nettoyage du graphe
    #graph = delete_low_degree_nodes(graph, 1, "deleted_nodes_3_2.txt")
    #graph = delete_isolated_nodes(graph)
    graph = delete_small_components(graph, 10)

    # Affichage des statistiques du graphe
    graph_stats(graph)
    nodes_stats(graph)
    
    #Création des différents graphes liés aux différentes méthodes de clustering
    graph = set_clusters(graph, "louvain")
    export_graph_to_gephi(graph, filename = "graph_louvain_del_small_comp.gexf")

    '''
    # Affichage des statistiques de clustering
    betweenness = nx.betweenness_centrality(graph)

    # Extraction des valeurs
    values = list(betweenness.values())

    # Affichage de l'histogramme
    plt.figure(figsize=(8,5))
    plt.hist(values, bins=20, color='skyblue', edgecolor='black')
    plt.title("Histogramme de la betweenness centrality")
    plt.xlabel("Betweenness centrality")
    plt.ylabel("Nombre de nœuds")
    plt.grid(axis='y', alpha=0.75)
    plt.show()

    # Calcul de l'eigenvector centrality
    eigenvector = nx.eigenvector_centrality(graph, max_iter=1000)

    # Extraction des valeurs
    values = list(eigenvector.values())

    # Affichage de l'histogramme
    plt.figure(figsize=(8,5))
    plt.hist(values, bins=20, color='lightcoral', edgecolor='black')
    plt.title("Histogramme de l'eigenvector centrality")
    plt.xlabel("Eigenvector centrality")
    plt.ylabel("Nombre de nœuds")
    plt.grid(axis='y', alpha=0.75)
    plt.show()

    # Calcul des degrés de chaque nœud
    degrees = [deg for _, deg in graph.degree()]

    # Affichage de l'histogramme
    plt.figure(figsize=(8,5))
    plt.hist(degrees, bins=range(min(degrees), max(degrees) + 2), edgecolor='black', align='left')
    plt.title("Histogramme des degrés du graphe")
    plt.xlabel("Degré")
    plt.ylabel("Nombre de nœuds")
    plt.grid(axis='y', alpha=0.7)
    plt.show()
    '''
    '''
    Autres méthodes de clustering
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