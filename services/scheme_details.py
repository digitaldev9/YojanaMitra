"""Read structured scheme details from attributed official pages."""

import re
from functools import lru_cache
from urllib.parse import urlsplit

import requests

from utils.helpers import official_host

HEADINGS = {
    "details": "overview", "overview": "overview", "description": "overview",
    "benefits": "benefits", "scholarship amount": "benefits",
    "eligibility": "eligibility", "eligibility criteria": "eligibility",
    "who is eligible": "audience", "who can apply": "audience", "target beneficiaries": "audience",
    "when to apply": "timing", "application period": "timing",
    "documents required": "documents", "required documents": "documents",
    "application process": "steps", "how to apply": "steps", "application procedure": "steps",
    "deadline": "deadline", "application deadline": "deadline",
}
LINK = re.compile(r"\[([^\]]+)\]\((https://[^)\s]+)\)")


def myscheme_page(url):
    parsed = urlsplit(url)
    return parsed.hostname in ("www.myscheme.gov.in", "myscheme.gov.in") and bool(
        re.fullmatch(r"/(?:[a-z]{2,3}/)?schemes/[^/]+/?", parsed.path)
    )


@lru_cache(maxsize=128)
def extract_page(url, api_key, cache_window):
    response = requests.post(
        "https://ydc-index.io/v1/extract",
        headers={"X-API-Key": api_key},
        json={"url": url, "full_page": {"extraction_formats": ["markdown"]}, "timeout": 12},
        timeout=(5, 16),
        allow_redirects=False,
    )
    response.raise_for_status()
    payload = response.json()
    if not official_host(payload.get("url", url)):
        raise ValueError("Extraction redirected outside official sources.")
    markdown = payload["contents"]["full_page"]["markdown"]
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("The official page returned no usable content.")
    return markdown


def parse_details(markdown):
    sections, tables = {}, []
    active = None
    rows = []
    application_url = None

    def flush_table():
        if len(rows) > 1 and all(len(row) == len(rows[0]) for row in rows):
            tables.append({"section": active, "headers": rows[0], "rows": rows[1:]})
        rows.clear()

    for raw in markdown.splitlines():
        value = raw.replace("\ufeff", "").strip()
        if re.fullmatch(r"(?:ok|iframe|was this helpful\??|show more|show less)", value, re.I):
            flush_table()
            if value.casefold().startswith("was this helpful"):
                active = None
            continue
        if "|" in value and active:
            row = [cell.strip() for cell in value.strip("|").split("|")]
            if len(row) > 1:
                if not all(re.fullmatch(r":?-{2,}:?", cell) for cell in row):
                    rows.append(row)
                continue
        flush_table()
        stripped = re.sub(r"^[#*•\s]+|[*:\s–-]+$", "", value).casefold()
        if stripped in {"sources and references", "frequently asked questions", "faqs",
                        "related schemes", "quick links", "important links", "user menu", "feedback"}:
            active = None
            continue
        section = HEADINGS.get(stripped)
        if stripped.startswith("the method of applying"):
            section = "steps"
        if section:
            active = section
            continue
        if value.startswith("#"):
            if active == "documents" and re.match(r"(?:for )?(?:fresh|renewal) application", stripped):
                sections.setdefault(active, []).append(value.lstrip("# ").rstrip("- "))
                continue
            if "scholarship scheme" in stripped and active is None and not sections:
                active = "overview"
            elif not (active == "steps" and re.match(r"step\s+\d", stripped)):
                active = None
            continue
        for label, href in LINK.findall(value):
            if official_host(href) and (active == "steps" or label.casefold().strip() in {"apply online", "application link", "apply now"}):
                if re.search(r"apply|application|mahadbt", label, re.I):
                    application_url = application_url or href
        if active and value and not re.fullmatch(r"[-*_\s]+", value):
            clean = LINK.sub(r"\1", value)
            clean = re.sub(r"^(?:[-*•]|\d+[.)])\s+", "", clean).replace("**", "")
            if clean and not clean.startswith(("<", "![")):
                sections.setdefault(active, []).append(clean)
    flush_table()
    return {key: list(dict.fromkeys(values)) for key, values in sections.items()}, tables, application_url
