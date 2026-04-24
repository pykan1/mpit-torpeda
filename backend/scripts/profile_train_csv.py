#!/usr/bin/env python3
"""
Quick profiler for anonymized trip CSV file.

Usage:
  python backend/scripts/profile_train_csv.py --path ./train.csv --sample 200000
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=Path("train.csv"))
    parser.add_argument("--sample", type=int, default=200000, help="Rows to scan (0 = full file)")
    args = parser.parse_args()

    if not args.path.exists():
        raise SystemExit(f"File not found: {args.path}")

    with args.path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        print(f"Columns ({len(columns)}): {', '.join(columns)}")

    non_empty = Counter()
    status_order = Counter()
    status_tender = Counter()
    city_ids = Counter()
    rows = 0

    with args.path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows += 1
            for col, value in row.items():
                if value not in ("", None):
                    non_empty[col] += 1
            city_ids[row.get("city_id", "")] += 1
            status_order[row.get("status_order", "")] += 1
            status_tender[row.get("status_tender", "")] += 1
            if args.sample and rows >= args.sample:
                break

    print(f"\nRows scanned: {rows}")
    print("\nFill ratio by column:")
    for col in columns:
        ratio = (non_empty[col] / rows) if rows else 0
        print(f"- {col}: {ratio:.3f}")

    print("\nTop city_id:", city_ids.most_common(10))
    print("status_order:", dict(status_order))
    print("status_tender (top 10):", status_tender.most_common(10))


if __name__ == "__main__":
    main()
