"""
Command Line Interface for ShorlyNot Skeleton Framework.
SIH 2026 PS 26141.
"""

import argparse
import json
import uuid
import uvicorn

from shorlynot_skeleton import __version__, __protocol__
from shorlynot_skeleton.pipeline import QuantumTransferPipeline
from shorlynot_skeleton.analysis.benchmark import QuantumBenchmark
from shorlynot_skeleton.models import TransactionPayload, TransferPipelineRequest, TauPreset


def main():
    parser = argparse.ArgumentParser(
        prog="shorlynot",
        description=f"ShorlyNot Quantum Security Framework CLI (v{__version__}, Protocol: {__protocol__})"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Start the Skeleton FastAPI server")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    # Command: benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Run Monte Carlo security and latency benchmarks")
    bench_parser.add_argument("--trials", type=int, default=100, help="Number of benchmark trials")
    bench_parser.add_argument("--output", type=str, default="docs/BENCHMARKS.md", help="Output report markdown path")

    # Command: transfer
    tx_parser = subparsers.add_parser("transfer", help="Execute single quantum-signed bank transfer")
    tx_parser.add_argument("--from-user", type=str, default="alice")
    tx_parser.add_argument("--to-user", type=str, default="bob")
    tx_parser.add_argument("--amount", type=float, default=1000.0)
    tx_parser.add_argument("--attack", type=str, default=None, choices=["forgery", "impersonation", "replay", "unauth_verify", "channel"])

    # Command: status
    subparsers.add_parser("status", help="Print current security stages and quantum status")

    args = parser.parse_args()

    if args.command == "serve":
        print(f"[*] Starting ShorlyNot Skeleton API on http://{args.host}:{args.port}")
        uvicorn.run("shorlynot_skeleton.api.app:app", host=args.host, port=args.port, reload=args.reload)
    elif args.command == "benchmark":
        bench = QuantumBenchmark(trials=args.trials)
        res = bench.run_full_suite()
        bench.generate_markdown_report(res, output_path=args.output)
    elif args.command == "transfer":
        pipeline = QuantumTransferPipeline()
        tx = TransactionPayload(
            from_user=args.from_user,
            to_user=args.to_user,
            amount=args.amount,
            currency="INR",
            tx_id=f"cli-tx-{uuid.uuid4().hex[:8]}"
        )
        req = TransferPipelineRequest(
            transaction=tx,
            signer_key_id=f"{args.from_user}-key-1",
            verifier_id="bob",
            tau_preset=TauPreset.NORMAL,
            simulate_attack=args.attack
        )
        res = pipeline.execute_transfer(req)
        print(json.dumps(res.model_dump(), indent=2))
    elif args.command == "status":
        pipeline = QuantumTransferPipeline()
        state = pipeline.stage_machine.get_state()
        print(json.dumps(state.model_dump(), indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
