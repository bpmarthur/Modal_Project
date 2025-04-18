# Modal_Project
Projet de modal de Arthur Fournier et Arthur Buis
lien du rapport : [https://plmlatex.math.cnrs.fr/project/67efd7b0e10d0157d64bfecd](https://plmlatex.math.cnrs.fr/read/hvtgtnmvykbn)
NLP Rapminerz : https://huggingface.co/rapminerz


Sites de BDD musicales :
- Music brainz : https://musicbrainz.org/artist/2c832944-52b6-428e-8d36-5d2cbc7121d9
documentation API : https://musicbrainz.org/doc/MusicBrainz_API
- Discogz : https://www.discogs.com/
doc API : https://www.discogs.com/developers/
- LAST-fm : https://www.last.fm/
doc API : https://www.last.fm/api
- Spotify API : https://developer.spotify.com/documentation/web-api/
- Genius API : https://docs.genius.com/

Logiciel de visualisation graphique de réseaux :
- Gephi : https://gephi.org/

Objectifs :
-	Identifier des clusters d’artistes musicaux et les afficher sur une carte, sur la base de collaborations musicales
  -	Relier la betweeness des artistes à leur nombre d'écoutes/stream
  -	Recherche de bridge : collaboration entre 2 genres ou 2 sous-genres différents
  -	Longueure moyenne d'un chemin entre 2 artistes
  -	Statistiques du graphe
- Étude des textes
  -	Rechercher de la similarité par embedding dans les textes des artistes, notamment pour donner un « thème » à chaque cluster. Nous disposons pour cela d'un modèle NLP entrainé sur des textes de rap français et son vocabulaire spécifique
  - Graphe où les sommets sont reliés en fonction de la proximité de leur langage (champs lexicaux, mots...)
  - Influence de la proximité linguistique sur les collaborations
  - Regarder l'originalité des artistes
-	Chercher des chaines de sources d’inspiration (trouver qui a inspiré qui, parmi les artistes dont on dispose de suffisamment de données)
-	Identifier les références faites à d'autres artistes dans les textes, de manière analogue à la chaine de sources d'inspirations
- Étude des textes
  -	Rechercher de la similarité par embedding dans les textes des artistes, notamment pour donner un « thème » à chaque cluster. Nous disposons pour cela d'un modèle NLP entrainé sur des textes de rap français et son vocabulaire spécifique
  - Graphe où les sommets sont reliés en fonction de la proximité de leur langage (champs lexicaux, mots...)
  - Influence de la proximité linguistique sur les collaborations
  - Regarder l'originalité des artistes
