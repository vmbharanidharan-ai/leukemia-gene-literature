# Leukemia gene ↔ literature pipeline

End-to-end flow:

1. **PubMed** — E-utilities search per gene + topic (with leukemia/AML synonyms).
2. **Claude** — grounded per-gene analysis (scores, pathways, **only PMIDs from retrieved records**).
3. **OpenAI (GPT)** — structured JSON + Markdown report (ranking, overlap narrative, references).

## Setup

```bash
cd leukemia-gene-literature
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Copy **`.env.example`** → **`.env`** and add your keys. Comments in `.env.example` point to where each key is obtained.

Required:

- `ANTHROPIC_API_KEY` — [Anthropic Console](https://console.anthropic.com/)
- `OPENAI_API_KEY` — [OpenAI API keys](https://platform.openai.com/api-keys)

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
| `claude_*.json` / `claude_all.json` | Per-gene Claude analysis |
| `structured_report.json` | GPT JSON (includes `markdown_report`) |
| `report.md` | Markdown report if present in structured output |

## Models

Override via environment (see `.env.example`):

- `CLAUDE_MODEL` (default: `claude-sonnet-4-20250514`)
- `OPENAI_MODEL` (default: `gpt-4o`)
