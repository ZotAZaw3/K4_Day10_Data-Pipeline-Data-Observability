from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import requests

from core.config import Settings

logger = logging.getLogger(__name__)

CROSSREF_WORKS_URL = "https://api.crossref.org/works"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 1.0


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _normalize_text(value: str | None) -> str:
    """Collapse whitespace, strip JATS tags. Never returns None."""
    if not value:
        return ""
    cleaned = re.sub(r"</?jats:[^>]+>", " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _extract_date_parts_str(node: dict | None) -> str:
    """Turn a Crossref Date/Partial Date node into 'YYYY', 'YYYY-MM', or
    'YYYY-MM-DD'. Handles missing node and null-filled date-parts safely."""
    if not node:
        return ""
    parts_list = node.get("date-parts") or []
    if not parts_list or not parts_list[0]:
        return ""
    parts = [p for p in parts_list[0] if p is not None]
    if not parts:
        return ""
    try:
        if len(parts) == 1:
            return f"{parts[0]:04d}"
        if len(parts) == 2:
            return f"{parts[0]:04d}-{parts[1]:02d}"
        return f"{parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d}"
    except (TypeError, ValueError):
        return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref /works payload into a list of PaperRecord.

    Records missing a DOI or a usable title are skipped as invalid.
    """
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        doi = item.get("DOI", "")
        if not doi:
            logger.warning("Skipping item with no DOI: %r", item.get("title"))
            continue

        title_list = item.get("title") or []
        title = _normalize_text(title_list[0]) if title_list else ""
        if not title:
            logger.warning("Skipping item %s: no usable title", doi)
            continue

        abstract = _normalize_text(item.get("abstract"))
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
            if a.get("given") or a.get("family")
        ]
        subjects = [s for s in (item.get("subject") or []) if s]

        published = _extract_date_parts_str(item.get("issued"))
        # Crossref has no "updated" concept for a work like arXiv does;
        # `deposited` (last metadata change) is the closest analog.
        updated = _extract_date_parts_str(item.get("deposited")) or published

        abs_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")

        pdf_url = ""
        for link in item.get("link", []) or []:
            content_type = (link.get("content-type") or "").lower()
            url = link.get("URL", "")
            if "pdf" in content_type or url.lower().endswith(".pdf"):
                pdf_url = url
                break

        record = PaperRecord(
            paper_id=doi,
            title=title,
            summary=abstract,
            authors=authors,
            categories=subjects,
            primary_category=subjects[0] if subjects else "",
            published=published,
            updated=updated,
            abs_url=abs_url,
            pdf_url=pdf_url,
            comment="",
        )
        records.append(record)

    return records


def _request_with_retry(params: dict) -> dict:
    backoff = INITIAL_BACKOFF_SECONDS
    last_exc: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(CROSSREF_WORKS_URL, params=params, timeout=30)
        except requests.RequestException as exc:
            last_exc = exc
            logger.warning(
                "Crossref request failed (attempt %d/%d): %s", attempt, MAX_RETRIES, exc
            )
        else:
            if response.status_code == 200:
                return response.json()
            if response.status_code in RETRYABLE_STATUS_CODES:
                logger.warning(
                    "Crossref returned retryable status %d (attempt %d/%d)",
                    response.status_code, attempt, MAX_RETRIES,
                )
                last_exc = requests.HTTPError(f"status {response.status_code}")
            else:
                response.raise_for_status()

        if attempt < MAX_RETRIES:
            time.sleep(backoff)
            backoff *= 2

    raise RuntimeError(f"Crossref request failed after {MAX_RETRIES} attempts") from last_exc


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch works from Crossref, cache the raw response, and parse into PaperRecord."""
    params = {
        "query": settings.source_query,
        "rows": settings.max_results,
    }
    if getattr(settings, "source_filter", None):
        params["filter"] = settings.source_filter

    payload = _request_with_retry(params)

    raw_path: Path = settings.paths.raw_api_response
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    records = parse_crossref_payload(payload)

    records_path: Path = settings.paths.raw_records_json
    records_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.write_text(
        json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("Fetched and parsed %d records", len(records))
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Load a JSON snapshot (written by fetch_source_records) back into PaperRecord."""
    data = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for entry in data:
        try:
            records.append(PaperRecord(**entry))
        except TypeError as exc:
            logger.warning("Skipping malformed record in %s: %s", path, exc)
            continue
    return records