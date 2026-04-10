"""CLI entrypoint for the literature pipeline."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from gene_lit.config import load_settings
from gene_lit.pipeline import run


def main(argv: Optional[List[str]] = None) -> None:
    p = argparse.ArgumentParser(
        description="PubMed → LLM per-gene analysis → LLM report (Gemini by default; optional OpenAI). See `.env.example`."
    )
    p.add_argument(
        "--genes",
        type=Path,
        required=True,
        help="CSV with a 'gene' column, or a .txt file with one gene symbol per line.",
    )
    p.add_argument(
        "--topic",
        required=True,
        help='Topic string, e.g. "acute myeloid leukemia progression"',
    )
    p.add_argument(
        "--max-papers",
        type=int,
        default=20,
        help="Max PubMed IDs to retrieve per gene (default: 20).",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs"),
        help="Directory for run outputs (default: ./outputs).",
    )
    args = p.parse_args(argv)

    if not args.genes.is_file():
        print(f"Genes file not found: {args.genes}", file=sys.stderr)
        sys.exit(1)

    settings = load_settings()
    out = run(
        args.genes,
        args.topic,
        max_papers=args.max_papers,
        output_dir=args.output_dir,
        settings=settings,
    )
    print(out)


if __name__ == "__main__":
    main()
