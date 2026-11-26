# Démo locale RAG — Clinique Dentaire Sourire, Nabeul

Démo fictive FR / arabe / darija tunisienne : Ollama (LFM3-1.7B et bge-m3), Flowise, FAISS local et n8n. La clinique, l'adresse, les tarifs et les coordonnées sont inventés; ne saisissez aucune donnée personnelle ou médicale. Le widget télécharge `flowise-embed` depuis jsDelivr et nécessite Internet pour cette bibliothèque.

## Diagnostic de cette machine

- PC : **MSI GF63 Thin 11SC**, processeur Intel Core i7-11800H.
- La propriété Windows `VirtualizationFirmwareEnabled` est **True** et `systeminfo` rapporte « Virtualisation activée dans le microprogramme : Oui ». La virtualisation CPU est donc activée; ne changez pas le BIOS sur la seule foi du message WSL.
- Cependant `wsl --status` affiche « WSL2 ne peut pas démarrer, car la virtualisation n'est pas activée sur cet ordinateur »; les distributions Ubuntu et `docker-desktop` sont arrêtées. La lecture des fonctionnalités Windows WSL/VirtualMachinePlatform nécessite PowerShell administrateur et n'a pas été possible dans cette session.
- `docker info` échoue encore : `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine ... The system cannot find the file specified.` Le diagnostic ne prouve pas que le BIOS bloque WSL; vérifier les composants Windows depuis une console administrateur.
- Le premier essai Ollama a échoué car C: n'avait que 85 Mio libres; le journal indique « Espace insuffisant sur le disque » lors de la copie de `cublasLt64_12.dll`. Le rollback de cet essai a réussi. Le second essai a installé Ollama sur D:. Après la tentative Build Tools, l'espace libre mesuré était **C: 0,38 Go**, **D: 169,82 Go**.
- Ollama **v0.40.18** est installé dans `D:\Ollama`; `OLLAMA_MODELS` est défini pour l'utilisateur sur `D:\Ollama\models`. LFM3 Q4_K_M et bge-m3 sont téléchargés. L'API `/api/tags` répond HTTP 200; le point d'API `/api/embed` a produit un vecteur bge-m3 de 1 024 dimensions.
- n8n **2.49.7** est installé sous `D:\ai-agency-tools\npm`; son interface locale a répondu HTTP 200 sur le port 5678. Le profil de cette session est stocké dans `D:\ai-agency-tools\n8n-data`.
- Node.js système : **v26.13.0**, npm **11.20.0**. Le package Flowise 3.1.4 déclare `engines.node = ^24`; une version portable **Node v24.22.3** est maintenant installée sur D: et son archive a été vérifiée avec le SHA256 officiel.
- Flowise **3.1.4** est maintenant installé localement dans `D:\ai-agency-tools\flowise-runtime` et démarre avec Node **24.22.3**. L'installation a nécessité `node-gyp@13.1.0` et `better-sqlite3@12.11.1`; le stub global `D:\ai-agency-tools\npm\flowise.cmd` n'est pas utilisable. L'interface a répondu HTTP 200 sur le port 3000. Le journal signale aussi `Cannot find module '@smithy/eventstream-codec'` lors du chargement du nœud AWS Bedrock; le serveur a poursuivi son démarrage et le scénario Ollama n'utilise pas ce nœud. FAISS n'a pas encore été testé.
- `D:\Ollama` est dans le PATH utilisateur, mais pas nécessairement dans l'environnement hérité par le terminal courant : préfixer le PATH de la session si la commande n'est pas trouvée. cloudflared n'est pas dans le PATH. Python 3.13 et Visual Studio Build Tools 2026 sont présents; aucun logiciel n'a été supprimé.

## Chemin recommandé maintenant : sans Docker

Ollama, Flowise et n8n sont installés et leurs interfaces/API locales ont répondu HTTP 200. Node 24.22.3 est présent sur D:. Aucun fichier n'a été supprimé et le BIOS n'a pas été modifié. L'installation antérieure de Build Tools 2022 n'a pas abouti, l'installateur exigeant au moins 3,51 Go libres sur C:.

### 1. Ollama et les modèles

Ollama a été installé dans `D:\Ollama` avec ses modèles dans `D:\Ollama\models`, ce qui a évité l'échec du premier essai sur C:. La variable `OLLAMA_MODELS` est persistée dans l'environnement utilisateur. L'installation ne doit pas être relancée. Dans un terminal dont le PATH n'a pas encore été actualisé, utiliser le chemin complet :

```powershell
$env:PATH = "D:\Ollama;$env:PATH"
& "D:\Ollama\ollama.exe" --version
& "D:\Ollama\ollama.exe" list
```

Les deux modèles ont été tirés et testés localement. Les premiers essais sans prompt ont montré une compréhension insuffisante de la darija tunisienne. Le prompt a été précisé pour reconnaître « قداش سوم ...؟ », imposer la devise DT et refuser brièvement les demandes hors périmètre. Avec un contexte fictif contrôlé, les essais directs à l'API Ollama ont répondu aux horaires en français, au tarif 40 DT en arabe et en darija tunisienne, et ont refusé la météo sans mentionner la clinique après le dernier ajustement. Aucune des réponses vérifiées ne contenait de balise de réflexion. Ces essais vérifient le modèle et le prompt seulement, pas la récupération RAG ni le critère global de 12/15.

```powershell
& "D:\Ollama\ollama.exe" run hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M "Bonjour, qui es-tu ?"
```

La fiche Hugging Face exige Ollama **v0.40.12 ou plus récent**. Flowise local accèdera à Ollama via `http://localhost:11434`; ne pas utiliser `host.docker.internal` dans ce mode. C: reste à faible capacité libre; aucun nettoyage automatique n'a été fait.

### 2. Rétablir WSL/Docker (facultatif pour ce chemin)

Dans **PowerShell administrateur**, lire l'état des composants avant d'envisager de les activer :

```powershell
foreach ($feature in @("Microsoft-Windows-Subsystem-Linux", "VirtualMachinePlatform")) {
    Get-WindowsOptionalFeature -Online -FeatureName $feature |
        Select-Object FeatureName, State
}
bcdedit /enum "{current}" | Select-String "hypervisorlaunchtype"
```

Ces commandes de diagnostic ne modifient pas les composants. Si une fonctionnalité est désactivée, l'activation peut demander un redémarrage; confirmer avant tout changement. Ne réinstallez pas Docker Desktop. Après résolution, vérifier `wsl --status`, `wsl -l -v` puis `docker info`. Le chemin Compose reste disponible ensuite.

### 3. Flowise et n8n localement

Node **24.x** est requis par Flowise 3.1.4; Node 26.13.0 présent sur la machine n'est pas accepté par la plage `^24`. Node v24.22.3 portable est installé dans `D:\node-v24.22.3-win-x64`. Flowise 3.1.4 a été installé dans `D:\ai-agency-tools\flowise-runtime`; la compilation de `better-sqlite3` a réussi avec les overrides `node-gyp@13.1.0` et `better-sqlite3@12.11.1`. Le répertoire est hors du dépôt. Ne pas utiliser le stub `D:\ai-agency-tools\npm\flowise.cmd`, qui échoue avec `MODULE_NOT_FOUND`.

```powershell
$env:PATH = "D:\node-v24.22.3-win-x64;$env:PATH"
$env:DATABASE_PATH = "D:\ai-agency-tools\flowise\data"
$env:BLOB_STORAGE_PATH = "D:\ai-agency-tools\flowise\storage"
$env:LOG_PATH = "D:\ai-agency-tools\flowise\logs"
& "D:\node-v24.22.3-win-x64\node.exe" "D:\ai-agency-tools\flowise-runtime\node_modules\flowise\bin\run" start
```

L'interface Flowise a répondu HTTP 200 sur `http://localhost:3000`. Son journal contient `Cannot find module '@smithy/eventstream-codec'` au chargement du nœud AWS Bedrock, mais le serveur a terminé son initialisation. Ce nœud n'est pas utilisé par le flux Ollama; corriger cette dépendance transitive si une fonctionnalité AWS est nécessaire. La compilation de FAISS sous Windows reste à tester.

n8n 2.49.7 est installé et a répondu HTTP 200 sur `http://localhost:5678`. Pour le redémarrer en local avec son profil sur D:, dans un autre terminal :

```powershell
$env:PATH = "D:\node-v24.22.3-win-x64;D:\ai-agency-tools\npm;$env:PATH"
$env:N8N_USER_FOLDER = "D:\ai-agency-tools\n8n-data"
$env:N8N_DIAGNOSTICS_ENABLED = "false"
$env:N8N_PERSONALIZATION_ENABLED = "false"
$env:N8N_VERSION_NOTIFICATIONS_ENABLED = "false"
& "D:\ai-agency-tools\npm\n8n.cmd" start
```

### 4. Construire et indexer le RAG local

Suivre [flowise/SETUP.md](./flowise/SETUP.md). Pour ce mode, choisir **FAISS**, enregistrer les fichiers d'index dans `E:\ai-agency\data\faiss`, et configurer ChatOllama et Ollama Embeddings sur `http://localhost:11434`. Faire manuellement l'Upsert depuis l'interface Flowise. Le magasin FAISS est local et persistant si son Base Path est renseigné.

Dans un nouveau terminal, définir l'URL locale et les identifiants Flowise sans les écrire dans un fichier :

```powershell
$env:FLOWISE_BASE_URL = "http://localhost:3000"
$env:FLOWISE_CHATFLOW_ID = "ID_DU_CHATFLOW"
$env:FLOWISE_API_KEY = "CLE_API_FLOWISE"
python .\scripts\test_chatbot.py
```

Le test envoie 15 questions (7 français, 3 arabe, 5 darija), produit `results\test_results.csv` et ne réussit que si le score est au moins 12/15 avec les 3 refus hors périmètre. Ce score et l'Upsert ne sont pas encore validés.

La page [web/index.html](./web/index.html) cible `http://localhost:3000` pour ce mode; remplacer son identifiant factice par le Chatflow ID.

## Chemin Docker ultérieur

Le [docker-compose.yml](./docker-compose.yml) est conservé : Qdrant, Flowise (port hôte 3001) et n8n (5678). Depuis `E:\ai-agency`, quand `docker info` répond correctement :

```powershell
docker compose up -d
Invoke-WebRequest http://localhost:3001
Invoke-WebRequest http://localhost:5678
Invoke-WebRequest http://localhost:6333/dashboard
```

Le Compose utilise `qdrant/qdrant:latest`, `flowiseai/flowise:3.1.4`, `docker.n8n.io/n8nio/n8n:latest`. Les tags Qdrant/n8n sont mobiles; noter les versions réellement tirées par `docker compose images`. Versions observées du client Docker et Compose : 29.9.3 et 5.7.1. Dans le mode conteneur, conserver Qdrant et les URL Ollama `http://host.docker.internal:11434` indiquées dans le guide.

## Checklist jour 1

- [x] Installer Ollama sur D:; vérifier la version, les deux modèles, une génération et un embedding bge-m3.
- [x] Tester directement le prompt système avec des questions FR, arabe, darija et hors périmètre, sur un contexte fictif contrôlé.
- [x] Installer n8n sur D: et vérifier l'interface locale HTTP 200.
- [ ] Confirmer l'état des fonctionnalités WSL/VirtualMachinePlatform depuis PowerShell administrateur.
- [x] Installer Node 24.22.3 portable sur D: et vérifier l'archive avec le SHA256 officiel.
- [x] Installer Flowise 3.1.4 localement et vérifier l'interface sur le port 3000 (HTTP 200).
- [ ] Construire le Chatflow, choisir FAISS avec Base Path persistant et faire l'Upsert.
- [ ] Lancer les 15 tests et atteindre 12/15 avec 3/3 refus; vérifier le widget.
- [ ] Réessayer Docker seulement si WSL fonctionne.

## Fichiers et limites

- [knowledge/clinique-dentaire-demo.md](./knowledge/clinique-dentaire-demo.md) contient exclusivement des renseignements fictifs; elle ne donne ni diagnostic, ni ordonnance, ni délai de remboursement.
- [prompts/system_prompt.txt](./prompts/system_prompt.txt) impose la réponse basée sur le contexte et les refus.
- `scripts/start.ps1` sert au démarrage Compose; le démarrage sans Docker se fait par les commandes locales ci-dessus. `scripts/tunnel.ps1` requiert cloudflared et expose Flowise sur Internet : ne l'utiliser que si nécessaire.
- Le widget charge une bibliothèque externe jsDelivr; l'application et le modèle sont locaux, mais cette page n'est pas entièrement hors ligne.
- Les essais directs montrent une compréhension insuffisante de la darija sans consignes explicites; les essais avec prompt et contexte contrôlé ont répondu au prix en dinars tunisiens. La validation de qualité du Chatflow reste à faire; le test par mots-clés est indicatif, pas une évaluation médicale.
# ai-agency
