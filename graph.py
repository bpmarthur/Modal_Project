from pymongo import MongoClient
import os
from bson.objectid import ObjectId
import networkx as nx

this_name = os.path.basename(__file__)

def build_graph(clientname, weighted = True):
    print(f"[{this_name}] Building graph...")
    #Récupération des données
    client = MongoClient("mongodb://localhost:27017/")
    db = client[clientname]  # nom de la base de données
    artists = db["artists"] 
    songs = db["songs"] 
    featurings = db["featurings"] 

    #Création du graphe
    G = nx.Graph()

    #On itère sur les artistes
    for artist in artists.find({}):
        print(f"[{this_name}] Adding artist {artist['name']} to graph{' '*100}", end ="\r")
        G.add_node(artist["id_genius"], name=str(artist["name"]), id_mongo=str(artist["_id"]), id_genius= int(artist["id_genius"]), id_mb = str(artist["id_mb"]), id_spotify=str(artist["id_spotify"]),url_genius = str(artist["url_genius"]))

    print(f"[{this_name}] All artists added to graph")
    #On itère sur les featurings de la chanson
    for featuring in featurings.find({}):
        
        node_1 = artists.find_one({"_id": featuring["artists"][0]})
        node_2 = artists.find_one({"_id": featuring["artists"][1]})
        print(f"\033[F[{this_name}] Adding featuring {featuring['title']} {node_1['name']} {node_2['name']} to graph{' '*100}", end ='')
        if G.has_edge(node_1['id_genius'], node_2['id_genius']):
            if weighted:
                G[node_1['id_genius']][node_2['id_genius']]["weight"] += 1
        else:
            G.add_edge(node_1['id_genius'], node_2['id_genius'], weight=1)
    
    print(f"[{this_name}] All featurings added to graph")
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
    graph = build_graph("musicdb", weighted = False)
    graph = delete_isolated_nodes(graph)
    graph_stats(graph)
    nodes_stats(graph)
    
    #Création des différents graphes liés aux différentes méthodes de clustering
    graph = set_clusters(graph, "louvain")
    export_graph_to_gephi(graph, filename = "graph_louvain.gexf")
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