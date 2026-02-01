from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import trafilatura

from app.core.config import settings
from app.models.schemas import OutputSchema
from app.services.cache import html_path, text_path
from app.services.dedupe import dedupe_items
from app.services.fetcher import PageFetcher
from app.services.openai_client import OpenAIClient
from app.services.query import generate_queries
from app.services.search.bing import BingSearchClient
from app.services.search.serpapi import SerpAPISearchClient
from app.utils.hashing import dedupe_key
from app.utils.text import clamp_quotes


AUTHORITATIVE_DOMAINS = {
    "gov.uk",
    "europa.eu",
    "consilium.europa.eu",
    "ec.europa.eu",
    "wto.org",
    "oecd.org",
    "imf.org",
}


def _credibility(url: str) -> str:
    host = urlparse(url).netloc.lower()
    for domain in AUTHORITATIVE_DOMAINS:
        if host.endswith(domain):
            return "high"
    return "medium"


def _source_name(url: str) -> str:
    host = urlparse(url).netloc
    return host.replace("www.", "")


def _metadata_from_html(html: Optional[str]) -> Dict[str, Optional[str]]:
    if not html:
        return {"title": None, "published_at": None}
    meta = trafilatura.extract_metadata(html)
    if not meta:
        return {"title": None, "published_at": None}
    title = meta.title if hasattr(meta, "title") else None
    date = meta.date if hasattr(meta, "date") else None
    return {"title": title, "published_at": date}


def _make_search_client():
    if settings.search_provider == "serpapi":
        return SerpAPISearchClient()
    return BingSearchClient()


def run_pipeline(run_id: str, params: Dict[str, Any]) -> tuple[OutputSchema, List[Dict[str, Any]]]:
    top_n = params.get("top_n_per_query", settings.top_n_per_query)
    recency_days = params.get("recency_days", settings.recency_days)
    categories = params.get("categories")
    dry_run = params.get("dry_run", settings.dry_run)
    max_items = params.get("max_items", settings.max_items)

    search_client = _make_search_client()
    fetcher = PageFetcher()
    llm = OpenAIClient()

    queries = generate_queries(categories)
    search_results = []
    for q in queries:
        search_results.extend(search_client.search(q, top_n=top_n, recency_days=recency_days))

    candidates: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []

    for result in search_results:
        fetched = fetcher.fetch_with_cache(run_id, result.url, dry_run=dry_run)
        meta = _metadata_from_html(fetched.html)
        title = meta.get("title") or result.title or ""
        published_at = meta.get("published_at")

        if not fetched.text:
            continue

        sources.append(
            {
                "url": result.url,
                "source_name": _source_name(result.url),
                "published_at": published_at,
                "credibility": _credibility(result.url),
                "html_path": str(html_path(run_id, result.url)),
                "text_path": str(text_path(run_id, result.url)),
            }
        )

        extracted = llm.extract_candidates(fetched.text, result.url, title, published_at)
        for item in extracted.get("items", []):
            quotes = clamp_quotes(item.get("evidence_quotes", []))
            candidates.append(
                {
                    **item,
                    "evidence": [
                        {
                            "source_name": _source_name(result.url),
                            "url": result.url,
                            "published_at": published_at,
                            "quote": q,
                            "credibility": _credibility(result.url),
                        }
                        for q in quotes
                    ],
                }
            )

    candidate_blob = {
        "items": candidates,
        "stats": {"found": len(candidates)},
    }

    synthesized = llm.synthesize(candidate_blob)
    items = synthesized.get("items", [])

    # Apply deterministic dedupe on top of synthesis
    texts = [f"{item.get('title','')} {item.get('summary','')}" for item in items]
    embeddings = llm.embed_texts(texts) if texts else []
    deduped = dedupe_items(items, embeddings)

    kept = deduped.items[:max_items]
    for item in kept:
        item["dedupe_key"] = item.get("dedupe_key") or dedupe_key(item.get("title", ""), item.get("summary", ""))
        if item.get("severity") == "high" and len(item.get("evidence", [])) < 2:
            item["confidence"] = min(float(item.get("confidence", 0.5)), 0.5)

    output = {
        "run_id": run_id,
        "scope": {"regions": ["UK", "EU"], "topic": "global trade challenges", "languages": ["en"]},
        "items": kept,
        "stats": {
            "found": len(candidates),
            "kept": len(kept),
            "duplicates_removed": deduped.duplicates_removed,
        },
    }
    return OutputSchema.model_validate(output), sources
