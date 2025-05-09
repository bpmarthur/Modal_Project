from pymongo import MongoClient
import csv
import networkx as nx

this_name = "graph.py"
def build_graph():
    print(f"[{this_name}] Building graph...")
    #Récupération des données
    client = MongoClient("mongodb://localhost:27017/")
    db = client["musicdb"]  # nom de la base de données
    artists = db["artists"] 
    songs = db["songs"] 
    featurings = db["featurings"] 

    #Création du graph
    G = nx.Graph()

    #On itère sur les artistes
    for artist in artists.find({}):
        G.add_node(artist["id_genius"], name=artist["name"], id=artist["_id"], id_genius=artist["id_genius"])

        #On itère sur les featurings de la chanson
        for featuring in featurings.find({}):
            G.add_node(featuring["featuring"], id=featuring["_id"], type="utilisateur")
            G.add_edge(song["title"], featuring["featuring"])

    return G
        
def export_graph_to_gephi(graph, filename = "graph.gexf"):
    print(f"[{this_name}] Exporting graph to Gephi...")
    nx.write_gexf(graph, filename)
    print(f"[{this_name}] Graph exported to {filename}")

if __name__ == "__main__":
    graph = build_graph()
    export_graph_to_gephi(graph)