"""Load gene lists from CSV or plain-text files."""

from __future__ import annotations

import csv
from pathlib import Path


def load_genes(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    lower = path.name.lower()
    if lower.endswith(".csv"):
        lines = text.splitlines()
        if not lines:
            return []
        reader = csv.DictReader(lines)
        fieldnames = reader.fieldnames or []
        for key in ("gene", "Gene", "symbol", "Symbol", "gene_symbol"):
            if key in fieldnames:
                return [row[key].strip() for row in reader if row.get(key, "").strip()]
        reader2 = csv.reader(lines)
        rows = list(reader2)
        if not rows:
            return []
        start = 1 if rows[0] and rows[0][0].lower() in ("gene", "symbol", "gene_symbol") else 0
        out: list[str] = []
        for r in rows[start:]:
            if r and r[0].strip():
                out.append(r[0].strip())
        return out
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
