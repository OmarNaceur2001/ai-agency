"""Inspect a local Flowise 3.1.4 instance without exposing credentials."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def get_json(base_url: str, path: str, api_key: str, timeout: int = 30) -> Any:
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
        method="GET",
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else None


def node_names(payload: Any) -> list[str]:
    candidates = payload.get("data", payload.get("nodes", [])) if isinstance(payload, dict) else payload
    if not isinstance(candidates, list):
        return []
    names = []
    for node in candidates:
        if isinstance(node, dict):
            name = node.get("name") or node.get("id") or node.get("label")
            if name:
                names.append(str(name))
    return sorted(set(names), key=str.casefold)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", action="store_true", help="Save provider and node metadata under results.")
    parser.add_argument("--base-url", default=os.environ.get("FLOWISE_BASE_URL", "http://localhost:3000"))
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    api_key = os.environ.get("FLOWISE_API_KEY", "").strip()
    if not api_key:
        print("FLOWISE_API_KEY is not set. Create a key in Flowise Settings → API Keys.", file=sys.stderr)
        return 2

    endpoints = {
        "version": "/api/v1/version",
        "nodes": "/api/v1/nodes",
        "chatflows": "/api/v1/chatflows",
        "document_loaders": "/api/v1/document-store/components/loaders",
        "embedding_providers": "/api/v1/document-store/components/embeddings",
        "vector_store_providers": "/api/v1/document-store/components/vectorstore",
    }
    report: dict[str, Any] = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "secret_values_written": False,
        "endpoints": {},
        "node_definitions": {},
    }
    failed = False

    for name, path in endpoints.items():
        try:
            payload = get_json(base_url, path, api_key)
            entry: dict[str, Any] = {"status": "ok", "path": path}
            if name == "nodes":
                names = node_names(payload)
                entry["count"] = len(names)
                entry["names"] = names
                report["endpoints"][name] = entry
                print(f"OK {path} — {len(names)} node definitions")

                # Fetch the concrete node schemas for the components relevant to this RAG flow.
                keywords = ("ollama", "faiss", "text", "markdown", "split", "retriev", "qa", "vectorstore")
                selected = [node for node in names if any(word in node.casefold() for word in keywords)]
                for node_name in selected:
                    node_path = "/api/v1/nodes/" + quote(node_name, safe="")
                    try:
                        report["node_definitions"][node_name] = get_json(base_url, node_path, api_key)
                        print(f"    schema OK: {node_name}")
                    except HTTPError as error:
                        report["node_definitions"][node_name] = {
                            "status": "http_error",
                            "http_status": error.code,
                            "path": node_path,
                        }
                        print(f"    schema unavailable: {node_name} (HTTP {error.code})")
                continue
            elif name == "chatflows":
                entry["chatflow_count"] = len(payload) if isinstance(payload, list) else None
                entry["payload_type"] = type(payload).__name__
                print(f"OK {path}")
            else:
                entry["providers"] = payload
                print(f"OK {path}")
            report["endpoints"][name] = entry
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            hint = "Check that the Bearer API key is valid." if error.code == 401 else (
                "The API key is valid but lacks permission for this endpoint." if error.code == 403 else
                "Check the endpoint against the installed Flowise build."
            )
            report["endpoints"][name] = {
                "status": "http_error", "http_status": error.code, "path": path,
                "detail": detail[:1000], "hint": hint,
            }
            print(f"FAIL HTTP {error.code} {path} — {hint}", file=sys.stderr)
            failed = True
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            report["endpoints"][name] = {"status": "error", "path": path, "error": str(error)}
            print(f"FAIL {path}: {error}", file=sys.stderr)
            failed = True

    if args.catalog:
        output_dir = Path(__file__).resolve().parents[1] / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "flowise-capabilities.json"
        output_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Capability report saved to {output_file}")

    if failed:
        print("Flowise API inspection incomplete. Resolve authentication/permissions before building or upserting.")
        return 1
    print("Flowise REST inspection completed. Use returned schemas and provider names as the source of truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
