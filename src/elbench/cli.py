from __future__ import annotations

import argparse
import asyncio
from datetime import datetime

from elbench.config import load_project_config
from elbench.execution import BenchmarkRunner, RunOptions
from elbench.registry import FileRegistry


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ELBench benchmark runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect resolved benchmark files")
    inspect_parser.add_argument("--config-root", default="configs")

    run_parser = subparsers.add_parser("run", help="Run benchmark")
    run_parser.add_argument("--config-root", default="configs")
    run_parser.add_argument("--model-id", required=True)
    run_parser.add_argument("--run-id", default=None)
    run_parser.add_argument("--module", action="append")
    run_parser.add_argument("--subset", action="append")
    run_parser.add_argument("--source-file", action="append")
    run_parser.add_argument("--dimension", action="append")
    run_parser.add_argument("--max-samples", type=int)
    run_parser.add_argument("--max-concurrency", type=int)
    run_parser.add_argument("--no-resume", action="store_true")
    run_parser.add_argument("--no-judge", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = load_project_config(args.config_root)

    if args.command == "inspect":
        registry = FileRegistry(config)
        resolved = registry.resolve()
        for item in resolved:
            print(
                f"module={item.entry.module} subset={item.entry.subset} file={item.entry.canonical_name} path={item.path}"
            )
        return

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    runner = BenchmarkRunner(config)
    result = asyncio.run(
        runner.run(
            RunOptions(
                model_id=args.model_id,
                run_id=run_id,
                modules=set(args.module) if args.module else None,
                subsets=set(args.subset) if args.subset else None,
                source_files=set(args.source_file) if args.source_file else None,
                dimensions=set(args.dimension) if args.dimension else None,
                max_samples=args.max_samples,
                max_concurrency=args.max_concurrency,
                resume=not args.no_resume,
                judge_enabled=not args.no_judge,
            )
        )
    )
    print(result)

