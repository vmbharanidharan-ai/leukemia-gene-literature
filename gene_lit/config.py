"""Load settings from environment. Missing required keys raise clear errors.

Fill in values in `.env` (copy from `.env.example`). Required keys:
  ANTHROPIC_API_KEY  — https://console.anthropic.com/
  OPENAI_API_KEY     — https://platform.openai.com/api-keys

Optional:
  NCBI_API_KEY       — https://www.ncbi.nlm.nih.gov/account/ (API Key Management)
  CONTACT_EMAIL      — your email (NCBI Entrez policy)
  CLAUDE_MODEL       — override default Claude model id
  OPENAI_MODEL       — override default OpenAI model name
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    openai_api_key: str
    ncbi_api_key: Optional[str]
    contact_email: str
    claude_model: str
    openai_model: str


def _req(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise RuntimeError(
            f"Missing required environment variable {name}. "
            f"Copy `.env.example` to `.env` and set {name}. "
            "See comments in `.env.example` for where to obtain keys."
        )
    return v


def _opt(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_settings() -> Settings:
    return Settings(
        anthropic_api_key=_req("ANTHROPIC_API_KEY"),
        openai_api_key=_req("OPENAI_API_KEY"),
        ncbi_api_key=_opt("NCBI_API_KEY") or None,
        contact_email=_opt("CONTACT_EMAIL") or "anonymous@example.com",
        claude_model=_opt("CLAUDE_MODEL") or "claude-sonnet-4-20250514",
        openai_model=_opt("OPENAI_MODEL") or "gpt-4o",
    )
