"""Load settings from environment. Missing required keys raise clear errors.

Fill in values in `.env` (copy from `.env.example`).

LLM_PROVIDER:
  gemini (default) — needs GEMINI_API_KEY (https://aistudio.google.com/apikey)
  openai           — needs OPENAI_API_KEY (https://platform.openai.com/api-keys)

Optional:
  NCBI_API_KEY   — https://www.ncbi.nlm.nih.gov/account/ (API Key Management)
  CONTACT_EMAIL  — recommended for NCBI Entrez policy
  OPENAI_MODEL   — default gpt-4o
  GEMINI_MODEL   — default gemini-1.5-flash
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load `.env` from the project root (next to pyproject.toml), not only from cwd,
# so `python -m gene_lit` works when the shell is not in this directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv()  # optional: also respect a `.env` in the current working directory


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    openai_api_key: Optional[str]
    gemini_api_key: Optional[str]
    ncbi_api_key: Optional[str]
    contact_email: str
    openai_model: str
    gemini_model: str


def _opt(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_settings() -> Settings:
    provider = (_opt("LLM_PROVIDER") or "gemini").lower()
    openai_key = _opt("OPENAI_API_KEY") or None
    gemini_key = _opt("GEMINI_API_KEY") or None

    if provider == "openai" and not openai_key:
        raw = os.environ.get("OPENAI_API_KEY")
        hint = ""
        if raw is not None and not str(raw).strip():
            hint = " Your `.env` has OPENAI_API_KEY= but the value is empty—paste the key after the = and save."
        raise RuntimeError(
            "LLM_PROVIDER=openai requires a non-empty OPENAI_API_KEY in `.env`."
            + hint
            + " See `.env.example`. "
            "To use Gemini instead, set LLM_PROVIDER=gemini and GEMINI_API_KEY."
        )
    if provider == "gemini" and not gemini_key:
        raw_g = os.environ.get("GEMINI_API_KEY")
        hint_g = ""
        if raw_g is not None and not str(raw_g).strip():
            hint_g = " Your `.env` has GEMINI_API_KEY= but the value is empty—paste the key after the = and save."
        raise RuntimeError(
            "LLM_PROVIDER=gemini requires a non-empty GEMINI_API_KEY in `.env`."
            + hint_g
            + " Create a key at https://aistudio.google.com/apikey"
        )
    if provider not in ("openai", "gemini"):
        raise RuntimeError(
            f"Invalid LLM_PROVIDER={provider!r}. Use 'openai' or 'gemini'."
        )

    return Settings(
        llm_provider=provider,
        openai_api_key=openai_key,
        gemini_api_key=gemini_key,
        ncbi_api_key=_opt("NCBI_API_KEY") or None,
        contact_email=_opt("CONTACT_EMAIL") or "anonymous@example.com",
        openai_model=_opt("OPENAI_MODEL") or "gpt-4o",
        gemini_model=_opt("GEMINI_MODEL") or "gemini-1.5-flash",
    )
