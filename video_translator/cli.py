from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import JobConfig
from .pipeline import run_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="video-translator")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    config_path = Path(args.config)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    config = JobConfig.from_dict(data)
    result = run_job(config)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

