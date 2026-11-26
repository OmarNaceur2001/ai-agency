"""Register admin user and login to Flowise, then explore the API."""
import json
import http.cookiejar
from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
from urllib.error import HTTPError

BASE = "http://localhost:3000"
cj = http.cookiejar.CookieJar()
opener = build_opener(HTTPCookieProcessor(cj))

# Step 1: Register
print("=== Registering ===")
reg_data = json.dumps({
    "username": "admin",
    "email": "admin@demo.local",
    "password": "Demo1234!"
}).encode()
try:
    req = Request(f"{BASE}/api/v1/account/register", data=reg_data,
                  headers={"Content-Type": "application/json"}, method="POST")
    resp = opener.open(req, timeout=15)
    body = json.loads(resp.read().decode())
    print(f"Register: {resp.status} -> {json.dumps(body, indent=2)[:500]}")
except HTTPError as e:
    body = e.read().decode()
    print(f"Register error: {e.code} -> {body[:500]}")

# Step 2: Login
print("\n=== Logging in ===")
login_data = json.dumps({
    "username": "admin@demo.local",
    "password": "Demo1234!"
}).encode()
try:
    req = Request(f"{BASE}/api/v1/auth/login", data=login_data,
                  headers={"Content-Type": "application/json"}, method="POST")
    resp = opener.open(req, timeout=15)
    body = json.loads(resp.read().decode())
    print(f"Login: {resp.status} -> {json.dumps(body, indent=2)[:500]}")
except HTTPError as e:
    body = e.read().decode()
    print(f"Login error: {e.code} -> {body[:500]}")

# Step 3: Show cookies
print("\n=== Cookies ===")
for c in cj:
    print(f"  {c.name}={c.value[:30]}...")

# Step 4: Try API with session
print("\n=== Testing API with session ===")
try:
    req = Request(f"{BASE}/api/v1/chatflows", method="GET")
    resp = opener.open(req, timeout=15)
    body = json.loads(resp.read().decode())
    print(f"Chatflows: {resp.status} -> {json.dumps(body, indent=2)[:300]}")
except HTTPError as e:
    body = e.read().decode()
    print(f"Chatflows error: {e.code} -> {body[:300]}")

# Step 5: Try listing nodes
try:
    req = Request(f"{BASE}/api/v1/nodes", method="GET")
    resp = opener.open(req, timeout=15)
    body = json.loads(resp.read().decode())
    # Just list node names
    names = [n.get("name", n.get("label", "?")) for n in body] if isinstance(body, list) else ["not a list"]
    print(f"\nNodes count: {len(body) if isinstance(body, list) else '?'}")
    # Find relevant nodes
    relevant = [n for n in names if any(k in n.lower() for k in ["ollama", "faiss", "text", "split", "retrieval", "qa", "conversation", "markdown", "memory"])]
    print(f"Relevant nodes: {relevant}")
except HTTPError as e:
    body = e.read().decode()
    print(f"Nodes error: {e.code} -> {body[:300]}")

# Step 6: Create API key
print("\n=== Creating API key ===")
try:
    apikey_data = json.dumps({"keyName": "demo-key"}).encode()
    req = Request(f"{BASE}/api/v1/apikey", data=apikey_data,
                  headers={"Content-Type": "application/json"}, method="POST")
    resp = opener.open(req, timeout=15)
    body = json.loads(resp.read().decode())
    apikey = body.get("apiKey", "")
    print(f"API key created: {body.get('keyName', '?')} / id={body.get('id', '?')}")
    print(f"API_KEY={apikey}")
except HTTPError as e:
    body = e.read().decode()
    print(f"API key error: {e.code} -> {body[:300]}")
