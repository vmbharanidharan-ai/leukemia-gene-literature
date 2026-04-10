"""End-to-end orchestration: PubMed → Claude → overlap stats → OpenAI structuring."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from gene_lit.claude_client import analyze_gene_literature
from gene_lit.config import Settings, load_settings
from gene_lit.io_util import load_genes
from gene_lit.openai_client import structure_findings
from gene_lit.pubmed import Paper, build_pubmed_query, fetch_medline_records, search_pubmed


def _pmid_to_genes_from_retrieval(gene_to_pmids: dict[str, list[str]]) -> dict[str, set[str]]:
    pmid_to_genes: dict[str, set[str]] = defaultdict(set)
    for gene, pmids in gene_to_pmids.items():
        for p in pmids:
            pmid_to_genes[p].add(gene)
    return dict(pmid_to_genes)


def compute_overlap(gene_to_pmids: dict[str, list[str]]) -> dict[str, Any]:
    genes = list(gene_to_pmids.keys())
    pmid_to_genes = _pmid_to_genes_from_retrieval(gene_to_pmids)
    multi = {p: sorted(gs) for p, gs in pmid_to_genes.items() if len(gs) > 1}
    pairs: dict[str, dict[str, Any]] = {}
    for i, g1 in enumerate(genes):
        for g2 in genes[i + 1 :]:
            a, b = set(gene_to_pmids[g1]), set(gene_to_pmids[g2])
            inter = a & b
            union = a | b
            jacc = len(inter) / len(union) if union else 0.0
            key = f"{g1}__{g2}"
            pairs[key] = {
                "gene_a": g1,
                "gene_b": g2,
                "shared_pmid_count": len(inter),
                "jaccard_pmids": round(jacc, 4),
                "shared_pmids": sorted(inter)[:50],
            }
    return {
        "genes": genes,
        "papers_mentioning_multiple_genes": multi,
        "pairwise": pairs,
        "total_unique_pmids": len(pmid_to_genes),
    }


def retrieve_for_gene(
    gene: str,
    topic: str,
    *,
    max_papers: int,
    settings: Settings,
) -> tuple[list[Paper], list[str]]:
    q = build_pubmed_query(gene, topic)
    pmids = search_pubmed(
        q,
        max_ids=max_papers,
        email=settings.contact_email,
        api_key=settings.ncbi_api_key,
    )
    papers = fetch_medline_records(
        pmids,
        email=settings.contact_email,
        api_key=settings.ncbi_api_key,
    )
    return papers, pmids


def run(
    genes_path: Path,
    topic: str,
    *,
    max_papers: int,
    output_dir: Path,
    settings: Optional[Settings] = None,
) -> Path:
    settings = settings or load_settings()
    genes = load_genes(genes_path)
    if not genes:
        raise RuntimeError(f"No genes found in {genes_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"run_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    gene_to_pmids: dict[str, list[str]] = {}
    retrieval_dump: list[dict[str, Any]] = []

    for gene in genes:
        papers, pmids = retrieve_for_gene(
            gene, topic, max_papers=max_papers, settings=settings
        )
        gene_to_pmids[gene] = pmids
        retrieval_dump.append(
            {
                "gene": gene,
                "query": build_pubmed_query(gene, topic),
                "pmids": pmids,
                "papers": [asdict(p) for p in papers],
            }
        )
        (run_dir / f"retrieval_{gene}.json").write_text(
            json.dumps(retrieval_dump[-1], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    (run_dir / "retrieval_all.json").write_text(
        json.dumps(retrieval_dump, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    overlap_stats = compute_overlap(gene_to_pmids)
    (run_dir / "overlap.json").write_text(
        json.dumps(overlap_stats, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    per_gene_analyses: list[dict[str, Any]] = []
    for block in retrieval_dump:
        gene = block["gene"]
        papers = [Paper(**p) for p in block["papers"]]
        if not papers:
            per_gene_analyses.append(
                {
                    "gene": gene,
                    "relevance_score": 1,
                    "evidence_strength": "low",
                    "summary": "No PubMed hits for the built query; widen topic or check gene symbol.",
                    "pathways": [],
                    "mutations_and_variants": [],
                    "clinical_relevance": "unknown",
                    "cited_pmids": [],
                    "note": "skipped_llm_no_papers",
                }
            )
            continue
        analysis = analyze_gene_literature(
            api_key=settings.anthropic_api_key,
            model=settings.claude_model,
            gene=gene,
            topic=topic,
            papers=papers,
        )
        per_gene_analyses.append(analysis)
        (run_dir / f"claude_{gene}.json").write_text(
            json.dumps(analysis, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    (run_dir / "claude_all.json").write_text(
        json.dumps(per_gene_analyses, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    structured = structure_findings(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        topic=topic,
        per_gene_analyses=per_gene_analyses,
        overlap_stats=overlap_stats,
    )
    (run_dir / "structured_report.json").write_text(
        json.dumps(structured, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    md = structured.get("markdown_report", "")
    if isinstance(md, str) and md.strip():
        (run_dir / "report.md").write_text(md, encoding="utf-8")

    return run_dir
