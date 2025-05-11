from pymongo import MongoClient
import os
from bson.objectid import ObjectId
import networkx as nx

this_name = os.path.basename(__file__)

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
        print(f"[{this_name}] Adding artist {artist['name']} to graph{' '*100}", end ="\r")
        G.add_node(artist["id_genius"], name=artist["name"], id=artist["_id"], id_genius=artist["id_genius"])

    print(f"[{this_name}] All artists added to graph")
    #On itère sur les featurings de la chanson
    for featuring in featurings.find({}):
        
        node_1 = artists.find_one({"_id": featuring["artists"][0]})
        node_2 = artists.find_one({"_id": featuring["artists"][1]})
        print(f"[{this_name}] Adding featuring {featuring['title']} {node_1['name']} {node_2['name']} to graph{' '*100}", end ='\r')
        if G.has_edge(node_1['id_genius'], node_2['id_genius']):
            G[node_1['id_genius']][node_2['id_genius']]["weight"] += 1
        else:
            G.add_edge(node_1['id_genius'], node_2['id_genius'], weight=1)
    
    print(f"[{this_name}] All featurings added to graph")
    return G
        
def export_graph_to_gephi(graph, filename = "graph.gexf"):
    print(f"[{this_name}] Exporting graph to Gephi...")
    nx.write_gexf(graph, filename)
    print(f"[{this_name}] Graph exported to {filename}")

if __name__ == "__main__":
    graph = build_graph()
    export_graph_to_gephi(graph)