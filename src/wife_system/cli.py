"""Command-line demonstration for the phase-0 agent core."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import uuid

from wife_system.agent.loop import AgentRunner
from wife_system.agent.providers import DeepSeekProvider, DeterministicBudgetProvider
from wife_system.tools import phase_zero_registry


def _positive_finite_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the phase-0 virtual finance agent.")
    parser.add_argument("message", nargs="?", default="查询本月虚拟预算")
    parser.add_argument("--provider", choices=("offline", "deepseek"), default="offline")
    parser.add_argument("--request-id", default=None)
    parser.add_argument("--timeout", type=_positive_finite_float, default=15.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.provider == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise SystemExit("DEEPSEEK_API_KEY is required for --provider deepseek.")
        provider = DeepSeekProvider(
            api_key=api_key,
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        )
    else:
        provider = DeterministicBudgetProvider()

    runner = AgentRunner(
        provider=provider,
        tools=phase_zero_registry(),
        provider_timeout_seconds=args.timeout,
    )
    result = runner.run(args.message, args.request_id or str(uuid.uuid4()))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return 0 if result.status.value == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
