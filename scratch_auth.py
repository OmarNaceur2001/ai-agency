"""Safe Flowise API diagnostic.

This replaces the old registration/login experiment. It never registers users,
tries default passwords, prints cookies, or prints API-key material.
"""

import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> int:
    base_url = os.environ.get("FLOWISE_BASE_URL", "http://localhost:3000").rstrip("/")
    api_key = os.environ.get("FLOWISE_API_KEY", "").strip()
    if not api_key:
        print("Set FLOWISE_API_KEY in the current shell after creating a key in Flowise Settings.")
        return 2
    request = Request(
        f"{base_url}/api/v1/nodes",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            print(f"Flowise nodes endpoint: HTTP {response.status}")
            print("Authentication succeeded. Response content was not printed.")
            return 0
    except HTTPError as error:
        print(f"Flowise returned HTTP {error.code}. Check the API key and its permissions.")
    except (URLError, TimeoutError) as error:
        print(f"Flowise is not reachable: {error}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
