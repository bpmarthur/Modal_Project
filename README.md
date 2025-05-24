# Projet de Modal CSC_43M02_EP - Exploration et apprentissage sur les graphes du Web : Analyse de collaborations musicales

Ce projet permet de manipuler, analyser et visualiser un graphe de collaborations entre artistes musicaux, à partir de données issues de Spotify, Genius, MusicBrainz et Last.fm. Il utilise Python, NetworkX et MongoDB pour construire le graphe, extraire et gérer les données avant de les exploiter avec Gephi.

Lien du rapport de notre modal : https://plmlatex.math.cnrs.fr/read/hvtgtnmvykbn

## Structure des fichiers

- **graph.py**  
  Construction et manipulation du graphe de collaborations.  
  Fonctions principales :
  - `build_graph` : Construit le graphe à partir de la base MongoDB.
  - `delete_isolated_nodes` / `delete_low_degree_nodes` : Supprime les nœuds isolés ou de faible degré.
  - `delete_small_components` : Supprime les composantes connexes de petite taille.
  - `set_clusters` : Attribue des clusters selon différentes méthodes (Louvain, clique, etc.).
  - `export_graph_to_gephi` : Exporte le graphe au format GEXF pour Gephi.
  - `graph_stats`, `nodes_stats`, `cluster_stats` : Affiche des statistiques sur le graphe.

- **update.py**  
  Gestion de la base MongoDB et mise à jour des données artistes/chansons.  
  Fonctions principales :
  - `update_mongo` : Met à jour la base d’artistes (import, enrichissement, liens Genius/MusicBrainz).
  - `update_featurings_and_songs_to_mongo` / `update_featurings_and_songs_to_mongo_v2` : Ajoute les collaborations (featurings) et chansons à la base.
  - `final_update` : Pipeline complet de mise à jour et enrichissement.
  - `update_json_to_mongo`, `update_csv_to_mongo` : Import de données depuis JSON ou CSV.
  - `fail_update_mongo` : Gestion des cas d’échec lors de la mise à jour.

- **spotify.py**  
  Fonctions pour interroger l’API Spotify (récupération d’artistes, followers, etc.).

- **genius.py**  
  Fonctions pour interroger l’API Genius (récupération d’ID, featurings, etc.).

- **musicbrainz.py**  
  Fonctions pour interroger la base de données MusicBrainz (récupération d’artistes, normalisation de noms, etc.) grâce à leur bibliothèque python.

- **tools.py**  
  Fonctions utilitaires (gestion des clés API, saisie utilisateur sécurisée, etc.).
  `get_key`, `int_response` : Utilitaires pour la gestion des clés et des entrées utilisateur.

- **embeddings.py**  
  Fonctions pour calculer et manipuler des embeddings d’artistes en utilisant notamment le modèle Word2Bezbar. Lien du modèle : https://huggingface.co/rapminerz/Word2Bezbar-large

- **graph_embedding.py**, **graph_lastfm.py**  
  Ces deux fichiers, similaires au fichier graph, permettent de construire le graphe de similarité Last.Fm et le graphe des embeddings.

- **data/**, **graphs/**  
  Dossiers de données (notamment le fichier csv des artistes), et le fichier des graphes exportés par graph.py, graph_embedding.py et graph_lastfm.py.


## Lancer le projet

1. **Installer les dépendances**  
   ```
   pip install pymongo networkx lyricsgenius musicbrainz
   ```

2. **Générer ou importer les données**  
   Depuis `update.py` :
   - Récupération des données depuis internet dans la base MongoDB *final_db* :
    ```python
    update_mongo(db_name = "final_db", update_embeddings=True)
    fail_update_mongo(db_name = "final_db", filename = "fail_final_update_mongo.txt")
    ```
   - Depuis un CSV :
    ```python
    update_csv_to_mongo(db_name="final_db")
    ```
    Puis récupération des featurings :
    ```python
    update_featurings_and_songs_to_mongo(db_name = "final_db")
    ```

4. **Générer le graphe**  
   Dans graph.py pour le graphe des collaborations :
    ```python
    graph = build_graph("final_db", weighted = True)

    # Nettoyage du graphe
    graph = delete_small_components(graph, 10)

    # Affichage des statistiques du graphe
    graph_stats(graph)
    nodes_stats(graph)
    
    #Clustering puis export du graphe
    graph = set_clusters(graph, "louvain")
    export_graph_to_gephi(graph, filename = "graph_louvain_final.gexf")
    ```

    Méthode similaire pour les fichiers graph_embedding.py et graph_lastfm.py.

5. **Visualiser dans Gephi**  
   Ouvrir le fichier `.gexf` du dossier graphs/ dans Gephi pour explorer le graphe.
