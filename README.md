# Local RAG demo — Clinique Dentaire Sourire

A local, fictional dental-clinic information assistant in French, Arabic and Tunisian darija. The clinic, address, phone number, opening hours, prices and procedures in the knowledge file are invented test data. Never enter real personal, patient, payment or medical information.

## Supported local stack

- Windows PowerShell; no Docker or WSL required.
- Ollama at http://localhost:11434:
  - Chat: hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M
  - Embeddings: bge-m3 (1,024 dimensions)
- Node 24.22.3 portable at D:\node-v24.22.3-win-x64.
- Flowise 3.1.4 at http://localhost:3000.
- n8n is installed but is not part of the RAG request path.
- The browser widget loads the pinned flowise-embed 3.1.6 bundle from jsDelivr; internet is required for that bundle.

The project deliberately does not try to repair WSL, Docker, BIOS settings, Windows features, or install additional runtimes.

## Disk-safe startup

The scripts use D: for temporary files, npm cache, Flowise database, blob storage and logs. They do not clean, delete, move or reset existing data. Keep the original Flowise database path consistent with the instance you intend to use.

From the repository root:

~~~powershell
$env:TEMP = "D:\temp"
$env:TMP = "D:\temp"
$env:npm_config_cache = "D:\npm-cache"
New-Item -ItemType Directory -Force D:\temp,D:\npm-cache | Out-Null

# Show disk space and verify the two existing Ollama models.
.\scripts\check_environment.ps1

# Start Flowise in the current terminal (Ctrl+C stops this process).
.\scripts\start.ps1
~~~

The default Flowise paths match the documented installation:
- DATABASE_PATH = D:\ai-agency-tools\flowise\data
- BLOB_STORAGE_PATH = D:\ai-agency-tools\flowise\storage
- LOG_PATH = D:\ai-agency-tools\flowise\logs

If the existing Flowise process was intentionally started with a different database path, stop it using the same terminal/process owner and set FLOWISE_DATABASE_PATH to that exact existing path before starting. Do not create a new database merely to bypass account authentication. The startup script refuses to launch a second Flowise process if port 3000 is already occupied.

## Flowise API authentication

Flowise 3.1.4 protects management REST routes with a Bearer API key. Create the key in the Flowise UI while signed in:

1. Open http://localhost:3000 and sign in using the existing administrator account.
2. Open Settings → API Keys → Create New Key.
3. Give it a descriptive name such as ai-agency-day1.
4. Grant only the permissions needed for this demo:
   - chatflows:create
   - chatflows:view
   - chatflows:update
   - documentStores:create
   - documentStores:view
   - documentStores:add-loader
   - documentStores:preview-process
   - documentStores:upsert-config
   - documentStores:update
5. Store the key in the current PowerShell session only. Do not commit it, put it in a .env file, paste it into chat, or place it in browser JavaScript.

~~~powershell
$secure = Read-Host "Flowise API key" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $env:FLOWISE_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    $secure.Dispose()
}
$env:FLOWISE_BASE_URL = "http://localhost:3000"

python scripts\check_flowise_api.py --catalog
~~~

The API inspection script checks the installed server, the node catalogue and Document Store component providers. It never prints the API key. A 401 means the key is absent/invalid; a 403 means the key lacks the permission for the endpoint. Do not attempt to bypass this by deleting or renaming the Flowise database.

## Build the RAG flow

Follow flowise/SETUP.md. The exact installed node definitions are obtained from the running Flowise 3.1.4 instance by check_flowise_api.py; do not guess node input names or submit guessed flowData to the create endpoint.

The intended graph is:
1. Markdown/Text File Loader.
2. Recursive Character Text Splitter, chunk size 500 and overlap 50.
3. Ollama Embeddings using bge-m3.
4. A local persistent vector store. Try FAISS first with base path E:\ai-agency\data\faiss. If FAISS cannot load, select only a persistent local provider actually returned by the installed Flowise catalogue. Do not silently switch to an in-memory store.
5. ChatOllama using hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M and temperature 0.1.
6. Conversational Retrieval QA Chain, with the system instructions in prompts/system_prompt.txt and the vector-store retriever connected to it.

Save a Chatflow named demo-clinique. Use Flowise's Upsert action to index knowledge/clinique-dentaire-demo.md. Confirm the upsert completes and run a vector-store query that returns relevant clinic chunks. The count reported by Flowise is the authoritative chunk count; do not estimate it from file length.

If the installed Flowise build does not expose one of the requested nodes or FAISS fails to load, stop and document the actual provider/node name and error. Do not install Visual Studio components, new runtimes, or packages globally without asking first.

## Smoke test and full evaluation

After creating and indexing the flow, set its ID in the current session:

~~~powershell
$env:FLOWISE_CHATFLOW_ID = "YOUR_REAL_CHATFLOW_ID"
$env:FLOWISE_BASE_URL = "http://localhost:3000"

# 2 French, 1 Arabic, 1 darija, 1 out-of-scope prediction.
python scripts\test_chatbot.py --smoke

# Run the unchanged 15-question evaluation.
python scripts\test_chatbot.py
~~~

The smoke subset is selected from the existing test set; no question, expected keyword or refusal marker is modified. The full run succeeds only at 12/15 or better and 3/3 out-of-scope refusals. CSV output is written to results/test_results.csv. Inspect failed questions and actual answers before changing one configuration variable per iteration.

## Browser widget (localhost only)

The browser must never receive the management API key. Configure the Chatflow to allow embedding from http://localhost:8080 (or the exact localhost origin shown by Flowise's UI). Do not attach a private Flowise API key to the public browser prediction path. In the Flowise process, CORS_ORIGINS and IFRAME_ORIGINS are set to the single local origin http://localhost:8080.

~~~powershell
$env:FLOWISE_CHATFLOW_ID = "YOUR_REAL_CHATFLOW_ID"
python scripts\configure_web.py

# In a second PowerShell window, from the repository root:
.\scripts\serve_web.ps1
~~~

Open http://localhost:8080. The page uses the exact pinned flowise-embed@3.1.6 version. web/config.js is generated locally and ignored by Git; it contains only the Chatflow ID, never an API key. If configuration is missing, the page displays a setup message instead of calling a placeholder ID.

## Tests and validation

~~~powershell
python -m unittest discover -s tests -v
python -m compileall -q scripts tests
~~~

The repository tests validate the project's static contract only. They do not prove that Flowise, FAISS, CORS, Ollama prediction, or the browser widget work on a particular machine. Keep these acceptance checks separate:
- Flowise root responds HTTP 200 on port 3000.
- Chatflow demo-clinique exists.
- Knowledge file is upserted; record the actual chunk count.
- Five smoke predictions pass.
- Full test scores at least 12/15 and all three refusal cases pass.
- Page returns HTTP 200 on port 8080 and a browser prediction succeeds.
- Check C: and D: free space at start and end.

## Optional Docker path

Docker Compose remains optional and is not used by the recommended local setup. Its published ports are bound to 127.0.0.1. Do not run it unless WSL/Docker has been independently repaired and the user explicitly chooses that path.

## Known limitations

- The Chatflow and vector index are runtime data in Flowise, not yet committed project artifacts. Export the saved flow from Flowise and review it before adding it to version control.
- The REST node catalogue is discoverable, but a reliable graph payload must be built from the installed node schemas. This repository does not ship a fabricated flowData file.
- FAISS has not been verified on this Windows installation. If it fails, record the exact error and use only a persistent local vector provider confirmed by the catalogue.
- The 15-question keyword evaluator is a small regression check, not a clinical safety or semantic-quality evaluation.
- All clinic content is fictitious. Do not use this demo with actual patients or clinical data.
