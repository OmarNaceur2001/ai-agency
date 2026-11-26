# Flowise 3.1.4 — build and verify the demo-clinique RAG flow

This guide is for the existing Windows installation. It deliberately preserves the current Flowise database and all existing files. It does not use Docker, WSL, cloudflared, a tunnel, or a database reset.

## 1. Start and inspect the installed instance

From the repository root, run check_environment.ps1 and start.ps1. Flowise must answer on http://localhost:3000 and Ollama on http://localhost:11434.

Create a Flowise API key in Settings → API Keys. The management key is required for protected REST routes. Put it in the current PowerShell environment as FLOWISE_API_KEY; never save it in this repository.

Required API-key permissions for the documented management operations:
- chatflows:create
- chatflows:view
- chatflows:update
- documentStores:create
- documentStores:view
- documentStores:add-loader
- documentStores:preview-process
- documentStores:upsert-config
- documentStores:update

Run:

~~~powershell
$env:FLOWISE_BASE_URL = "http://localhost:3000"
python scripts\check_flowise_api.py --catalog
~~~

This calls the actual Flowise 3.1.4 endpoints for nodes, chatflows and Document Store providers, then writes a non-secret capability snapshot under results. The exact node names, labels and input parameters returned by this instance are authoritative. If a required node/provider is absent, stop and record that fact rather than inventing a node definition.

## 2. Create the vector index

In Flowise, open Document Stores (or the vector-store upsert interface exposed by the installed build) and create a store named demo-clinique-kb.

1. Add knowledge/clinique-dentaire-demo.md as the source document. Use a Markdown/Text loader actually available in the component catalogue.
2. Select Recursive Character Text Splitter. Set chunk size to 500 and chunk overlap to 50.
3. Select Ollama Embeddings. Base URL: http://localhost:11434. Model: bge-m3.
4. Try FAISS first. Set its persistent Base Path to E:\ai-agency\data\faiss. The path must not be blank or in-memory.
5. If FAISS does not load, do not install anything. Inspect the vector-store providers in results/flowise-capabilities.json and choose only a local, persistent provider already present in this Flowise installation. Record its exact provider name and storage path. Do not use an in-memory provider, and do not select Qdrant unless the optional Docker service is actually available.
6. Preview the chunks, then run Upsert. Wait for a successful completion response.
7. Record the chunk count reported by Flowise. Query the vector store with a phrase such as “horaires le samedi” and verify that relevant chunks from the fictional knowledge file are returned.

The Flowise 3.1.4 source exposes Document Store REST routes under /api/v1/document-store. The upsert route is POST /api/v1/document-store/upsert/{storeId}; the vector config routes are under /api/v1/document-store/vectorstore. These operations have multipart/configuration-specific request bodies. Use the UI to create the store and processing configuration unless you have captured the exact request schema from this installed version. Do not send a guessed JSON body.

## 3. Build the conversational Chatflow

Create a Chatflow named demo-clinique. Use the installed node definitions from the capability snapshot; labels vary by Flowise component version, so use the returned node name and inputs instead of assuming field names.

Required nodes:
- ChatOllama: model hf.co/LiquidAI/LFM3-1.7B-GGUF:Q4_K_M, base URL http://localhost:11434, temperature 0.1.
- Conversational Retrieval QA Chain.
- The retriever connected to the persistent vector store created above.
- A system instruction copied from prompts/system_prompt.txt. The instructions must remain context-grounded, prohibit diagnosis/medication/prescriptions, refuse unrelated topics briefly, and explicitly treat all clinic facts/prices as fictitious.

Conceptual connections:
- Ollama Embeddings (bge-m3) → vector store embeddings input.
- Markdown/Text loader → Recursive Character Text Splitter → vector store documents input (indexing/upsert path).
- Persistent vector store → Vector Store Retriever → Conversational Retrieval QA Chain retriever input.
- ChatOllama → Conversational Retrieval QA Chain language-model input.

Use the actual connector/port handles shown in Flowise. If the installed version exposes the vector store and retrieval chain in a different shape, follow its node configuration UI and inspect the node definitions; do not force incompatible edges or submit guessed flowData.

Save the Chatflow. Copy its real ID to FLOWISE_CHATFLOW_ID. If Flowise offers an allowed-domain or embed-domain list, allow only http://localhost:8080 for this local demo. Do not place the management API key in the browser. If the Chatflow is configured to require a flow-specific API key, the embed page cannot safely contain that secret; configure the local public/embed access with the exact domain allowlist instead.

## 4. Smoke test and full evaluation

~~~powershell
$env:FLOWISE_BASE_URL = "http://localhost:3000"
$env:FLOWISE_CHATFLOW_ID = "PASTE_THE_REAL_CHATFLOW_ID"
python scripts\test_chatbot.py --smoke
python scripts\test_chatbot.py
~~~

Smoke checks are 2 French questions, 1 Arabic question, 1 Tunisian-darija question and 1 out-of-scope question. The smoke threshold is 5/5 and 1/1 refusal.

The full regression set is unchanged. Acceptance is at least 12/15 and 3/3 refusals. Review results/test_results.csv. If a test fails, keep its original question and expected markers unchanged. Change one of: prompt wording, retriever top-K (3–6), chunk configuration, temperature, or the explicit context-only refusal instruction. Log each run and keep the best complete configuration. Maximum five iterations.

## 5. Configure the local embed page

The startup script sets:
- HOST=127.0.0.1
- PORT=3000
- CORS_ORIGINS=http://localhost:8080
- IFRAME_ORIGINS=http://localhost:8080

Generate the browser config from the Chatflow ID:

~~~powershell
$env:FLOWISE_CHATFLOW_ID = "PASTE_THE_REAL_CHATFLOW_ID"
python scripts\configure_web.py
~~~

This writes web/config.js, which is Git-ignored. It contains the Chatflow ID only. Then run serve_web.ps1; it serves the web folder on 127.0.0.1:8080. Verify the page responds HTTP 200 and make one real prediction through the widget in the browser. The API management key must never appear in config.js, HTML, browser storage or network headers from the page.

## 6. Versioned export

After the Chatflow works, export it from Flowise UI and review the exported JSON for credential material, local absolute paths and API-key references before committing. Do not export or commit secrets. Keep the current database and existing Flowise data as-is.
