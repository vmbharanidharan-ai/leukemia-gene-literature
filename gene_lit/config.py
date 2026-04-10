"""Load settings from environment. Missing required keys raise clear errors.

Fill in values in `.env` (copy from `.env.example`).

LLM_PROVIDER:
  openai (default) — needs OPENAI_API_KEY (https://platform.openai.com/api-keys)
  gemini          — needs GEMINI_API_KEY only; free tier via Google AI Studio
                     https://aistudio.google.com/apikey
                     pip install google-generativeai (or: pip install -e ".[gemini]")

Optional:
  NCBI_API_KEY   — https://www.ncbi.nlm.nih.gov/account/ (API Key Management)
  CONTACT_EMAIL  — recommended for NCBI Entrez policy
  OPENAI_MODEL   — default gpt-4o
  GEMINI_MODEL   — default gemini-1.5-flash
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


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
    provider = (_opt("LLM_PROVIDER") or "openai").lower()
    openai_key = _opt("OPENAI_API_KEY") or None
    gemini_key = _opt("GEMINI_API_KEY") or None

    if provider == "openai" and not openai_key:
        raise RuntimeError(
            "LLM_PROVIDER=openai requires OPENAI_API_KEY. "
            "Set it in `.env` (see `.env.example`). "
            "For a free-tier option, set LLM_PROVIDER=gemini and GEMINI_API_KEY from "
            "https://aistudio.google.com/apikey"
        )
    if provider == "gemini" and not gemini_key:
        raise RuntimeError(
            "LLM_PROVIDER=gemini requires GEMINI_API_KEY. "
            "Create a free key at https://aistudio.google.com/apikey and add it to `.env`."
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
