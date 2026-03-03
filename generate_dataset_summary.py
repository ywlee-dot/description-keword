#!/usr/bin/env python3
import argparse
import sys
from typing import List
import os
import json

from dataset_summary import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    generate_summaries,
    read_csv_rows_from_path,
    read_rows_from_path,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate dataset keywords/description from xlsx.")
    parser.add_argument("--input", required=True, help="Path to input xlsx file")
    parser.add_argument("--output", required=True, help="Path to output json file")
    parser.add_argument("--sheet", default=None, help="Sheet name (xlsx only, default: active)")
    parser.add_argument("--header-start", default=None, help="Header start cell (e.g. A1)")
    parser.add_argument("--header-end", default=None, help="Header end cell (e.g. G2)")
    parser.add_argument("--org-name", default=None, help="Organization name for prompt template")
    parser.add_argument("--debug", action="store_true", help="Include header debug info in output")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="LLM API base URL")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="LLM model name")
    parser.add_argument("--sleep", type=float, default=0.0, help="Seconds to sleep between calls")
    parser.add_argument("--include-row", action="store_true", help="Include input row in output")
    parser.add_argument(
        "--group-key",
        default=None,
        help="Header name to group rows (default: first column)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Missing GEMINI_API_KEY/OPENAI_API_KEY env var.", file=sys.stderr)
        return 2

    header_range = None
    if args.header_start and args.header_end:
        header_range = (args.header_start, args.header_end)
    header_debug = None
    if args.input.endswith(".csv"):
        if args.debug:
            rows, header_debug = read_csv_rows_from_path(
                args.input, header_range=header_range, return_debug=True
            )
        else:
            rows = read_csv_rows_from_path(args.input, header_range=header_range)
    else:
        if args.debug:
            rows, header_debug = read_rows_from_path(
                args.input, args.sheet, header_range=header_range, return_debug=True
            )
        else:
            rows = read_rows_from_path(args.input, args.sheet, header_range=header_range)
    if not rows:
        print("No rows found.", file=sys.stderr)
        return 1

    results: List[dict] = generate_summaries(
        rows,
        args.group_key,
        args.base_url,
        api_key,
        args.model,
        include_rows=args.include_row,
        sleep_seconds=args.sleep,
        org_name=args.org_name,
        header_debug=header_debug if args.debug else None,
    )

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Wrote {len(results)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
