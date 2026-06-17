"""Download Ty's Duke Bass Connections oyster data into data/raw/.

Usage:
    python scripts/fetch_data.py                 # 2024-2025 CSVs (default)
    python scripts/fetch_data.py --year 2025     # also fetch 2025-2026 XLSX files

Reads URLs from config/sources.yaml. Only downloads files that are listed there.
"""
from __future__ import annotations

import argparse
import os
import sys

import requests
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"  GET {url}")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    with open(dest, "wb") as f:
        f.write(r.content)
    print(f"      -> {dest} ({len(r.content):,} bytes)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", choices=["2024", "2025", "both"], default="2024",
                    help="2024 = 2024-2025 CSVs; 2025 = 2025-2026 XLSX; both = all")
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "raw"))
    args = ap.parse_args()

    with open(os.path.join(ROOT, "config", "sources.yaml"), encoding="utf-8") as f:
        sources = yaml.safe_load(f)
    ty = sources["ty_oyster"]

    if args.year in ("2024", "both"):
        base = ty["raw_base_2024_2025"]
        print("Fetching 2024-2025 (CSV)...")
        for _, rel in ty["files_2024_2025"].items():
            _download(f"{base}/{rel}", os.path.join(args.out, os.path.basename(rel)))

    if args.year in ("2025", "both"):
        base = ty["raw_base_2025_2026"]
        print("Fetching 2025-2026 (XLSX)...")
        for _, rel in ty["files_2025_2026"].items():
            if rel and not rel.endswith("}"):  # skip the pattern entry
                _download(f"{base}/{rel}", os.path.join(args.out, os.path.basename(rel)))

    print("Done.")


if __name__ == "__main__":
    main()
