# Configuration du Chatflow Flowise

Ce guide décrit une configuration manuelle dans Flowise; aucun Chatflow n'est créé automatiquement. Les noms exacts des nœuds peuvent varier légèrement selon la version installée.

## Choisir le mode de stockage

- **Sans Docker (mode local recommandé sur cette machine)** : remplacer Qdrant par **FAISS**, donner un Base Path persistant tel que `E:\ai-agency\data\faiss`, puis relier documents et embeddings à FAISS. Laisser Base Path vide stocke l'index en mémoire et le perd au redémarrage. La documentation Flowise signale que l'installation npm de FAISS sur Windows nécessite Visual Studio Build Tools et Python.
- **Avec Docker** : utiliser Qdrant à `http://qdrant:6333`, collection `demo_clinic`, comme décrit ci-dessous.

## 1. Créer le flux et charger le document

1. Ouvrir Flowise sur `http://localhost:3000` sans Docker, ou `http://localhost:3001` avec Docker; créer un **Chatflow** et lui donner un nom de démonstration.
2. Ajouter un nœud **Text File** et sélectionner `E:\ai-agency\knowledge\clinique-dentaire-demo.md` (ou charger le fichier depuis l'interface).
3. Ajouter **Recursive Text Splitter** et définir `Chunk Size = 500` et `Chunk Overlap = 50`. Relier la sortie du chargeur au splitter.

## 2. Configurer les embeddings et le magasin vectoriel

1. Ajouter **Ollama Embeddings**; définir le modèle `bge-m3`. Utiliser `http://localhost:11434` sans Docker, ou `http://host.docker.internal:11434` depuis Flowise en conteneur.
2. Pour une installation locale, ajouter **FAISS**, définir son **Base Path** sur `E:\ai-agency\data\faiss`, puis relier les documents découpés et les embeddings à ses entrées correspondantes.
3. Pour Docker, ajouter **Qdrant**, utiliser l'URL `http://qdrant:6333` et la collection `demo_clinic`, puis relier les documents et embeddings aux entrées correspondantes.
4. Utiliser le même modèle d'embeddings pour l'indexation et la recherche.

## 3. Construire la chaîne de conversation

1. Ajouter **ChatOllama** avec le modèle `hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M`, l'URL `http://localhost:11434` sans Docker ou `http://host.docker.internal:11434` en conteneur, et une température de `0.1`.
2. Ajouter **Conversational Retrieval QA Chain**. Connecter ChatOllama au modèle de la chaîne et FAISS ou Qdrant au retriever.
3. Définir le prompt système de la chaîne en copiant le contenu de `E:\ai-agency\prompts\system_prompt.txt`. Vérifier que la chaîne injecte le contexte récupéré et conserve l'historique conversationnel.
4. Enregistrer le flux. Copier son identifiant (Chatflow ID) pour le test et la page web. Garder l'accès local; ne pas publier de clé dans un fichier.

## 4. Upsert — étape à effectuer dans l'interface

Dans le Chatflow, ouvrir le panneau de chargement/indexation ou l'action d'**Upsert** du magasin vectoriel choisi, sélectionner `clinique-dentaire-demo.md`, vérifier le splitter et lancer **Upsert**. Avec Qdrant, vérifier la collection `demo_clinic`; avec FAISS, vérifier le Base Path `E:\ai-agency\data\faiss`. Attendre la confirmation de fin dans Flowise avant de tester les questions.

L'Upsert n'est pas lancé par les scripts du dépôt. Vérifier ensuite une question simple sur les horaires et une question hors périmètre avant la démo.
