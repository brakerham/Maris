"""Export the production FastAPI contract in a deterministic form."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from wife_system.api.production import create_production_openapi_app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    schema = create_production_openapi_app().openapi()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(schema, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
