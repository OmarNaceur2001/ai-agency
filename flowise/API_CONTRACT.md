# Flowise 3.1.4 API contract notes

These route names were checked against the Flowise upstream source tag flowise@3.1.4. This file records route contracts; it does not claim that an API call has succeeded against the local Windows instance.

## Authentication and permissions

The server's global API middleware validates an Authorization: Bearer <API_KEY> header for protected /api/v1 routes. Create the key in the Flowise UI while signed in. The key is workspace-scoped and its permissions are checked again by individual route handlers.

Relevant route permissions:
- Chatflow create/list/read/update: chatflows:create, chatflows:view, chatflows:update.
- Document Store create/read/update: documentStores:create, documentStores:view, documentStores:update.
- Loader discovery and processing: documentStores:add-loader, documentStores:preview-process.
- Vector-store configuration and insertion: documentStores:upsert-config.

The node routes do not add a route-level permission check, but the global API-key middleware still protects /api/v1/nodes.

## Relevant endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/v1/version | Version/health probe; whitelisted by Flowise |
| GET | /api/v1/nodes | List installed node definitions |
| GET | /api/v1/nodes/{name} | Read one installed node schema |
| GET | /api/v1/chatflows | List existing chatflows |
| POST | /api/v1/chatflows | Create a chatflow from valid Flowise graph data |
| PUT | /api/v1/chatflows/{id} | Update an existing chatflow |
| POST | /api/v1/document-store/store | Create a Document Store |
| GET | /api/v1/document-store/store | List Document Stores |
| GET | /api/v1/document-store/components/loaders | Discover document loaders |
| GET | /api/v1/document-store/components/embeddings | Discover embedding providers |
| GET | /api/v1/document-store/components/vectorstore | Discover vector-store providers |
| POST | /api/v1/document-store/upsert/{id} | Upsert Document Store content; request may include multipart files/config |
| POST | /api/v1/document-store/vectorstore/query | Query a configured Document Store vector store |
| POST | /api/v1/prediction/{chatflowId} | Execute a saved chatflow prediction |

The server source marks prediction and public-chatflow routes as whitelisted. If a flow has a flow-specific API key configured, prediction validation still checks that key. The management API key must not be put in browser code.

## Why graph creation remains UI-first

The POST /api/v1/chatflows controller accepts a Flowise ChatFlow object and stores its flowData. The graph must contain node IDs, node data, component names, versions, input values, edge IDs and valid source/target handles. Those values are tied to the node schemas returned by the running installation. A guessed graph payload can save successfully but fail at execution time.

The project therefore reads GET /api/v1/nodes and GET /api/v1/nodes/{name}, then documents the UI build path in SETUP.md. Once a valid flow has been saved and exported from this exact Flowise installation, a subsequent automation can replay that reviewed export through the REST API.

## CORS and iframe policy

Flowise 3.1.4 reads:
- CORS_ORIGINS as a comma-separated list of allowed browser origins.
- IFRAME_ORIGINS as a comma-separated list used by the CSP frame-ancestors header.

The local start script sets both to http://localhost:8080 and binds Flowise to 127.0.0.1:3000. No wildcard origin, public tunnel, or API secret in the browser is configured.
