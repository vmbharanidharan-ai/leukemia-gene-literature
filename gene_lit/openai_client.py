"""OpenAI: structure multi-gene results, overlap narrative, final report."""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI


def structure_findings(
    *,
    api_key: str,
    model: str,
    topic: str,
    per_gene_analyses: list[dict[str, Any]],
    overlap_stats: dict[str, Any],
) -> dict[str, Any]:
    client = OpenAI(api_key=api_key)
    payload = {
        "topic": topic,
        "per_gene_analyses": per_gene_analyses,
        "overlap_statistics": overlap_stats,
    }
    instructions = """You integrate per-gene literature analyses into one structured report.

Rules:
- Preserve all PMID citations that appear in per_gene_analyses; do not invent PMIDs or DOIs.
- Rank genes by scientific relevance to the topic using the provided relevance_score and overlap stats.
- Highlight shared biology (pathways/themes) when overlap_statistics supports it.
- Be concise but precise.

Return JSON with keys:
- "executive_summary": string (short)
- "ranked_genes": array of objects with keys gene, rank, rationale, top_pmids (array of strings)
- "overlap_highlights": array of strings (cross-gene themes)
- "limitations": string (e.g., abstract-only, query bias)
- "markdown_report": string (full report in Markdown, with a References section listing unique PMIDs cited)
"""

    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)
