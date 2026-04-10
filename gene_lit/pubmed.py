"""PubMed search and fetch via NCBI E-utilities (Biopython Entrez)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable, Optional

from Bio import Entrez, Medline


@dataclass(frozen=True)
class Paper:
    pmid: str
    title: str
    abstract: str
    journal: str
    year: str
    doi: Optional[str]


def _configure_entrez(email: str, api_key: Optional[str]) -> None:
    Entrez.email = email
    Entrez.api_key = api_key


def _throttle(has_api_key: bool) -> None:
    # Stay under NCBI limits: 3/s without key, 10/s with key (burst-safe pause between genes).
    time.sleep(0.35 if not has_api_key else 0.12)


def search_pubmed(
    term: str,
    *,
    max_ids: int,
    email: str,
    api_key: Optional[str],
) -> list[str]:
    _configure_entrez(email, api_key)
    _throttle(api_key is not None)
    handle = Entrez.esearch(db="pubmed", term=term, retmax=max_ids, sort="relevance")
    record = Entrez.read(handle)
    handle.close()
    id_list = record.get("IdList", [])
    return [str(i) for i in id_list]


def fetch_medline_records(
    pmids: Iterable[str],
    *,
    email: str,
    api_key: Optional[str],
) -> list[Paper]:
    pmids = list(pmids)
    if not pmids:
        return []
    _configure_entrez(email, api_key)
    _throttle(api_key is not None)
    handle = Entrez.efetch(db="pubmed", id=",".join(pmids), rettype="medline", retmode="text")
    records = list(Medline.parse(handle))
    handle.close()
    out: list[Paper] = []
    for rec in records:
        pmid = rec.get("PMID", "")
        if not pmid:
            continue
        title = " ".join(rec.get("TI", [])) if isinstance(rec.get("TI"), list) else str(rec.get("TI", ""))
        abstract = " ".join(rec.get("AB", [])) if isinstance(rec.get("AB"), list) else str(rec.get("AB", ""))
        journal = str(rec.get("JT", rec.get("TA", "")))
        year = ""
        dp = rec.get("DP", "")
        if isinstance(dp, str) and dp:
            year = dp.split()[0]
        elif isinstance(dp, list) and dp:
            year = str(dp[0]).split()[0]
        aid = rec.get("AID", [])
        doi = None
        if isinstance(aid, list):
            for a in aid:
                if isinstance(a, str) and "[doi]" in a:
                    doi = a.replace(" [doi]", "").strip()
                    break
        elif isinstance(aid, str) and "[doi]" in aid:
            doi = aid.replace(" [doi]", "").strip()
        out.append(
            Paper(
                pmid=str(pmid),
                title=title.strip(),
                abstract=abstract.strip(),
                journal=journal.strip(),
                year=year.strip(),
                doi=doi,
            )
        )
    return out


def build_pubmed_query(gene: str, topic: str) -> str:
    """Combine gene, user topic, and common leukemia synonyms for recall."""
    g = gene.strip()
    topic_clean = topic.strip().replace('"', "")
    synonyms = "leukemia OR AML OR ALL OR CML OR myeloid OR lymphoid OR hematologic malignancy"
    return (
        f'({g}[Title/Abstract]) AND (("{topic_clean}"[Title/Abstract]) OR {synonyms})'
    )
