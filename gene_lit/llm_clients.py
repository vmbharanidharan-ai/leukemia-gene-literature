"""Literature analysis and final structuring via OpenAI or Google Gemini."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from openai import OpenAI

from gene_lit.pubmed import Paper

_ANALYSIS_SYSTEM = (
    "You are a biomedical literature analyst. "
    "Only use information from the provided paper records. "
    "Return a single JSON object matching the requested schema."
)

_STRUCTURE_SYSTEM = """You integrate per-gene literature analyses into one structured report.

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


def _parse_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("Model response did not contain a JSON object")
    return json.loads(m.group(0))


def _analysis_user_prompt(
    gene: str, topic: str, allowed_pmids: set[str], catalog: list[dict[str, Any]]
) -> str:
    return f"""Gene: {gene}
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


def analyze_gene_literature_openai(
    *,
    api_key: str,
    model: str,
    gene: str,
    topic: str,
    papers: list[Paper],
) -> dict[str, Any]:
    allowed_pmids = {p.pmid for p in papers}
    catalog = [
        {
            "pmid": p.pmid,
            "doi": p.doi,
            "title": p.title,
            "year": p.year,
            "journal": p.journal,
            "abstract": p.abstract[:12000],
        }
        for p in papers
    ]
    user = _analysis_user_prompt(gene, topic, allowed_pmids, catalog)
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _ANALYSIS_SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    content = resp.choices[0].message.content or "{}"
    data = json.loads(content)
    cited = [str(x) for x in data.get("cited_pmids", [])]
    data["cited_pmids"] = [c for c in cited if c in allowed_pmids]
    data["gene"] = gene
    return data


def analyze_gene_literature_gemini(
    *,
    api_key: str,
    model: str,
    gene: str,
    topic: str,
    papers: list[Paper],
) -> dict[str, Any]:
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError(
            "google-generativeai is required for Gemini. "
            'Run: pip install -e .   (or: pip install "google-generativeai>=0.8.0")'
        ) from e

    allowed_pmids = {p.pmid for p in papers}
    catalog = [
        {
            "pmid": p.pmid,
            "doi": p.doi,
            "title": p.title,
            "year": p.year,
            "journal": p.journal,
            "abstract": p.abstract[:12000],
        }
        for p in papers
    ]
    user = _analysis_user_prompt(gene, topic, allowed_pmids, catalog)
    genai.configure(api_key=api_key)
    gm = genai.GenerativeModel(
        model_name=model,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
        system_instruction=_ANALYSIS_SYSTEM,
    )
    response = gm.generate_content(user)
    text = response.text or "{}"
    data = _parse_json_object(text)
    cited = [str(x) for x in data.get("cited_pmids", [])]
    data["cited_pmids"] = [c for c in cited if c in allowed_pmids]
    data["gene"] = gene
    return data


def analyze_gene_literature(
    *,
    provider: str,
    gene: str,
    topic: str,
    papers: list[Paper],
    openai_api_key: Optional[str],
    openai_model: str,
    gemini_api_key: Optional[str],
    gemini_model: str,
) -> dict[str, Any]:
    p = provider.strip().lower()
    if p == "gemini":
        if not gemini_api_key:
            raise RuntimeError("LLM_PROVIDER=gemini requires GEMINI_API_KEY in .env")
        return analyze_gene_literature_gemini(
            api_key=gemini_api_key,
            model=gemini_model,
            gene=gene,
            topic=topic,
            papers=papers,
        )
    if p == "openai":
        if not openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai requires OPENAI_API_KEY in .env")
        return analyze_gene_literature_openai(
            api_key=openai_api_key,
            model=openai_model,
            gene=gene,
            topic=topic,
            papers=papers,
        )
    raise RuntimeError(f"Unknown LLM_PROVIDER={provider!r}; use 'openai' or 'gemini'.")


def structure_findings_openai(
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
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _STRUCTURE_SYSTEM},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
    )
    content = resp.choices[0].message.content or "{}"
    return json.loads(content)


def structure_findings_gemini(
    *,
    api_key: str,
    model: str,
    topic: str,
    per_gene_analyses: list[dict[str, Any]],
    overlap_stats: dict[str, Any],
) -> dict[str, Any]:
    try:
        import google.generativeai as genai
    except ImportError as e:
        raise RuntimeError(
            "google-generativeai is required for Gemini. "
            'Run: pip install -e .   (or: pip install "google-generativeai>=0.8.0")'
        ) from e

    genai.configure(api_key=api_key)
    payload = json.dumps(
        {
            "topic": topic,
            "per_gene_analyses": per_gene_analyses,
            "overlap_statistics": overlap_stats,
        },
        ensure_ascii=False,
    )
    gm = genai.GenerativeModel(
        model_name=model,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
        system_instruction=_STRUCTURE_SYSTEM,
    )
    response = gm.generate_content(
        "Integrate the following data into the JSON schema described in your instructions:\n" + payload
    )
    text = response.text or "{}"
    return _parse_json_object(text)


def structure_findings(
    *,
    provider: str,
    topic: str,
    per_gene_analyses: list[dict[str, Any]],
    overlap_stats: dict[str, Any],
    openai_api_key: Optional[str],
    openai_model: str,
    gemini_api_key: Optional[str],
    gemini_model: str,
) -> dict[str, Any]:
    p = provider.strip().lower()
    if p == "gemini":
        if not gemini_api_key:
            raise RuntimeError("LLM_PROVIDER=gemini requires GEMINI_API_KEY in .env")
        return structure_findings_gemini(
            api_key=gemini_api_key,
            model=gemini_model,
            topic=topic,
            per_gene_analyses=per_gene_analyses,
            overlap_stats=overlap_stats,
        )
    if p == "openai":
        if not openai_api_key:
            raise RuntimeError("LLM_PROVIDER=openai requires OPENAI_API_KEY in .env")
        return structure_findings_openai(
            api_key=openai_api_key,
            model=openai_model,
            topic=topic,
            per_gene_analyses=per_gene_analyses,
            overlap_stats=overlap_stats,
        )
    raise RuntimeError(f"Unknown LLM_PROVIDER={provider!r}; use 'openai' or 'gemini'.")
