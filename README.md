# Leukemia Gene Literature Pipeline

This project turns a **gene list + topic** into a literature-backed summary for leukemia research.

It automatically:

- queries PubMed for each gene and topic,
- analyzes retrieved evidence with an LLM,
- ranks genes by relevance,
- computes cross-gene overlap,
- and writes machine-readable + human-readable reports.

## Purpose

Use this pipeline when you want a fast first-pass answer to:

- Which genes in my list look most relevant to a leukemia biology question?
- What does recent literature say for each gene?
- Which PMIDs support those findings?
- Where do genes overlap in evidence and themes?

This is designed for hypothesis generation and triage, not clinical decision-making.

## How It Works

1. **Retrieve (PubMed)**  
   Build gene-specific search queries and fetch PMIDs, titles, journals, years, and abstracts.

2. **Analyze (LLM per gene)**  
   Generate structured outputs for each gene: relevance score, evidence strength, summary, pathways, variants, clinical notes, and cited PMIDs.

3. **Integrate (LLM global report)**  
   Combine all per-gene analyses into a ranked report with overlap highlights and references.

4. **Save artifacts**  
   Store intermediate and final files under `outputs/run_<timestamp>/`.

## Inputs and Outputs

### Inputs

- **Genes file**: CSV with a `gene` column, or plain text (one gene symbol per line)
- **Topic**: free-text query (example: `acute myeloid leukemia progression`)

### Outputs

| File | Contents |
|------|----------|
| `retrieval_*.json` / `retrieval_all.json` | Queries, PMIDs, abstracts |
| `overlap.json` | Pairwise shared-PMID overlap and Jaccard scores |
| `analysis_*.json` / `per_gene_analyses.json` | Per-gene LLM analysis |
| `structured_report.json` | Final integrated JSON |
| `report.md` | Markdown summary report |

## LLM Providers

| `LLM_PROVIDER` | API key | Notes |
|----------------|---------|-------|
| **`gemini`** (default) | `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey), free tier available |
| `openai` | `OPENAI_API_KEY` | [OpenAI API keys](https://platform.openai.com/api-keys) |

## Quick Start

```bash
cd leukemia-gene-literature
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Then edit `.env` and set at least:

- `LLM_PROVIDER=gemini` (or `openai`)
- matching key (`GEMINI_API_KEY` or `OPENAI_API_KEY`)

Recommended:

- `NCBI_API_KEY` for higher PubMed request limits
- `CONTACT_EMAIL` for NCBI Entrez policy compliance

## Run

```bash
python -m gene_lit --genes data/sample_genes.csv --topic "acute myeloid leukemia progression" --max-papers 15
```

## Configuration

Common environment variables in `.env`:

- `LLM_PROVIDER` (`gemini` default, or `openai`)
- `GEMINI_MODEL` (default: `gemini-2.5-flash`)
- `OPENAI_MODEL` (default: `gpt-4o`)
- `GEMINI_DELAY_SEC` (default: `6`) to reduce burst traffic
- `NCBI_API_KEY` (optional but recommended)
- `CONTACT_EMAIL` (recommended)

## Troubleshooting

### Gemini `429 RESOURCE_EXHAUSTED` / quota errors

The pipeline retries with backoff, but you can still exceed daily free-tier limits.

Try:

- waiting for quota reset,
- increasing `GEMINI_DELAY_SEC` (example: `15`),
- reducing `--max-papers`,
- using fewer genes per run,
- switching `GEMINI_MODEL` to another available model from [Gemini models](https://ai.google.dev/gemini-api/docs/models),
- enabling billing if needed.

### Gemini `404 model not found`

Set `GEMINI_MODEL` to a currently available model id from [Gemini models](https://ai.google.dev/gemini-api/docs/models).

### OpenAI `insufficient_quota`

Your key is valid but your OpenAI project has no available quota/billing.

### Python warnings (3.9)

You may see deprecation warnings from Google client libraries on Python 3.9.  
The pipeline can still run, but upgrading to Python 3.10+ is recommended.

## Notes

- `.env` is gitignored; keep real keys there, not in `.env.example`.
- Results are literature-grounded summaries and may omit full-text-only findings.
- Treat outputs as research support; always validate critical claims in source papers.
