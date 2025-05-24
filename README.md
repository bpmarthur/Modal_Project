# Projet : Analyse de collaborations musicales

Ce projet permet de manipuler, analyser et visualiser un graphe de collaborations entre artistes musicaux, à partir de données issues de Spotify, Genius, MusicBrainz et Last.fm. Il utilise Python, NetworkX et MongoDB pour construire le graphe, extraire des statistiques, gérer les données et exporter les résultats pour Gephi.

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
  Fonctions pour interroger l’API MusicBrainz (récupération d’artistes, normalisation de noms, etc.).

- **tools.py**  
  Fonctions utilitaires (gestion des clés API, saisie utilisateur sécurisée, etc.).
  `get_key`, `int_response` : Utilitaires pour la gestion des clés et des entrées utilisateur.

- **embeddings.py**  
  Fonctions pour calculer et manipuler des embeddings d’artistes (Word2Vec).

- **graph_embedding.py**, **graph_lastfm.py**  
  Fonctions avancées pour l’analyse de graphes et l’intégration de données Last.fm.
  Ces deux fichiers, similaires au fichier graph, permettent de construire le graphe de similarité Last.Fm et le graphe des embeddings.

- **data/**, **graphs/**  
  Dossiers de données (notamment le fichier csv des artistes), et le fichier des graphes exportés par graph.py, graph_embedding.py et graph_lastfm.py.


## Lancer le projet

1. **Installer les dépendances**  
   Assure-toi d’avoir Python 3, MongoDB, et les packages suivants :
   ```
   pip install pymongo networkx
   ```
   (ajoute aussi les dépendances pour les API si besoin)

2. **Lancer MongoDB**  
   Démarre le serveur MongoDB local.

3. **Importer les données**  
   Utilise les fonctions d’import dans `update.py` :
   - Depuis un CSV :
     ```python
     from update import update_csv_to_mongo
     update_csv_to_mongo(db_name="final_db")
     ```
   - Depuis un JSON :
     ```python
     from update import update_json_to_mongo
     update_json_to_mongo(db_name="final_db")
     ```

4. **Mettre à jour la base et générer le graphe**  
   Exemple :
   ```python
   from update import update_featurings_and_songs_to_mongo_v2
   update_featurings_and_songs_to_mongo_v2(db_name="final_db")
   ```

   Puis, pour générer et exporter le graphe :
   ```python
   from graph import build_graph, delete_small_components, export_graph_to_gephi
   G = build_graph("final_db")
   G = delete_small_components(G, min_size=10)
   export_graph_to_gephi(G, filename="graph_final.gexf")
   ```

5. **Visualiser dans Gephi**  
   Ouvre le fichier `.gexf` dans Gephi pour explorer le graphe.

