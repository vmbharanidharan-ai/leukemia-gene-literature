"""Claude: literature-grounded analysis per gene."""

from __future__ import annotations

import json
import re
from typing import Any

import anthropic

from gene_lit.pubmed import Paper


def _extract_json_block(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    m = re.search(r"\{[\s\S]*\}\s*$", text)
    if not m:
        raise ValueError("Claude response did not contain a JSON object")
    return json.loads(m.group(0))


def analyze_gene_literature(
    *,
    api_key: str,
    model: str,
    gene: str,
    topic: str,
    papers: list[Paper],
) -> dict[str, Any]:
    allowed_pmids = {p.pmid for p in papers}
    catalog = []
    for p in papers:
        catalog.append(
            {
                "pmid": p.pmid,
                "doi": p.doi,
                "title": p.title,
                "year": p.year,
                "journal": p.journal,
                "abstract": p.abstract[:12000],
            }
        )
    user = f"""Gene: {gene}
Topic focus: {topic}

You are given PubMed-derived records. PMIDs you may cite MUST be from this list only: {sorted(allowed_pmids)}

Paper records (JSON):
{json.dumps(catalog, ensure_ascii=False)}

Return a single JSON object with keys:
- "gene": string (same as input)
- "relevance_score": number from 1-10 (how central this gene is to the topic based ONLY on these excerpts)
- "evidence_strength": one of "high", "medium", "low"
- "summary": string, 2-4 sentences
- "pathways": array of short strings (inferred from text; empty if unclear)
- "mutations_and_variants": array of short strings (only if mentioned)
- "clinical_relevance": string (short; "unknown" if not discussed)
- "cited_pmids": array of strings — subset of allowed PMIDs that best support your summary (max 8)

Do not invent PMIDs. If evidence is thin, lower the score and say so in summary."""

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        temperature=0.2,
        system=(
            "You are a biomedical literature analyst. "
            "Only use information from the provided paper records. "
            "Output valid JSON only, no markdown fences."
        ),
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    data = _extract_json_block(text)
    cited = [str(x) for x in data.get("cited_pmids", [])]
    data["cited_pmids"] = [c for c in cited if c in allowed_pmids]
    data["gene"] = gene
    return data
