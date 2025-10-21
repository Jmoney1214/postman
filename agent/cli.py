import argparse
import json
import sys
from pathlib import Path

from .agent import LiquorStoreMarketingAgent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LiquorStoreMarketingAgent CLI",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "data" / "demo"),
        help="Directory containing input data files (JSON)",
    )
    parser.add_argument(
        "--request-type",
        type=str,
        required=True,
        choices=[
            "campaign_idea",
            "performance_review",
            "promo_optimization",
            "content_creation",
        ],
        help="Type of agent request to handle",
    )
    parser.add_argument(
        "--payload",
        type=str,
        default="{}",
        help="JSON string payload with additional parameters",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="-",
        help="Path to write agent output; '-' for stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    payload: dict
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON for --payload: {e}", file=sys.stderr)
        return 2

    agent = LiquorStoreMarketingAgent()
    agent.ingest_data(data_dir)

    output_text = agent.handle_request(args.request_type, payload)

    if args.output == "-":
        print(output_text)
    else:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_text, encoding="utf-8")
        print(f"Wrote output to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
