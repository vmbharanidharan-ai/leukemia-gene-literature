# Leukemia gene ↔ literature pipeline

End-to-end flow:

1. **PubMed** — E-utilities search per gene + topic (with leukemia/AML synonyms).
2. **LLM (same provider for both steps)** — per-gene grounded analysis (scores, pathways, **only PMIDs from retrieved records**).
3. **Same LLM** — structured JSON + Markdown report (ranking, overlap narrative, references).

## Providers

| `LLM_PROVIDER` | API key | Notes |
|----------------|---------|--------|
| `openai` (default) | `OPENAI_API_KEY` | [OpenAI API keys](https://platform.openai.com/api-keys) |
| `gemini` | `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) — free tier suitable for experimentation |

For Gemini, install the extra dependency:

```bash
pip install -e ".[gemini]"
```

## Setup

```bash
cd leukemia-gene-literature
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
# If using Gemini:
pip install -e ".[gemini]"
```

Copy **`.env.example`** → **`.env`** and set `LLM_PROVIDER` plus the matching key.

Optional:

- `NCBI_API_KEY` — [NCBI account](https://www.ncbi.nlm.nih.gov/account/) → API Key Management (higher PubMed rate limits)
- `CONTACT_EMAIL` — recommended for NCBI Entrez policy

## Run

```bash
python -m gene_lit --genes data/sample_genes.csv --topic "acute myeloid leukemia progression" --max-papers 15
```

Outputs go to `outputs/run_<timestamp>/`:

| File | Contents |
|------|-----------|
| `retrieval_*.json` / `retrieval_all.json` | Queries, PMIDs, abstracts |
| `overlap.json` | Shared PMIDs, pairwise Jaccard |
| `analysis_*.json` / `per_gene_analyses.json` | Per-gene LLM analysis |
| `structured_report.json` | Final JSON (includes `markdown_report`) |
| `report.md` | Markdown report if present |

## Models

Override via environment (see `.env.example`):

- `OPENAI_MODEL` (default: `gpt-4o`)
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)
