"""Generate the local browser config using a Chatflow ID (never an API secret)."""

import argparse
import os
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Replace an existing generated config.js.")
    args = parser.parse_args()

    chatflow_id = os.environ.get("FLOWISE_CHATFLOW_ID", "").strip()
    if not chatflow_id:
        parser.error("FLOWISE_CHATFLOW_ID must contain the real saved Chatflow ID.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", chatflow_id):
        parser.error("FLOWISE_CHATFLOW_ID contains unexpected characters or has an invalid length.")

    config_path = Path(__file__).resolve().parents[1] / "web" / "config.js"
    if config_path.exists() and not args.force:
        raise SystemExit(f"{config_path} already exists. Review it first; rerun with --force only to replace it.")

    config_path.write_text(
        "// Generated locally by scripts/configure_web.py. Do not add secrets here.\n"
        f"window.FLOWISE_CONFIG = Object.freeze({{ chatflowId: {chatflow_id!r} }});\n",
        encoding="utf-8",
    )
    print(f"Created {config_path}")
    print("Only the Chatflow ID was written. No API key or password was written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
