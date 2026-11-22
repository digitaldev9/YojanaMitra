from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import requests

from utils.helpers import official_host


SEARCH_URL = "https://ydc-index.io/v1/search"


class ResearchError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    description: str
    highlights: tuple[str, ...]


def parse_search(payload: object) -> list[Source]:
    if not isinstance(payload, dict):
        raise ResearchError("You.com returned an unexpected response.")
    results = payload.get("results", {})
    if not isinstance(results, dict):
        raise ResearchError("You.com returned an unexpected results format.")
    rows = results.get("web", [])
    if not isinstance(rows, list):
        raise ResearchError("You.com returned an unexpected web results format.")
    sources = []
    valid_rows = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        title, url = row.get("title"), row.get("url")
        if not isinstance(title, str) or not title.strip() or not isinstance(url, str):
            continue
        valid_rows += 1
        if not official_host(url):
            continue
        contents = row.get("contents")
        highlights = contents.get("highlights") if isinstance(contents, dict) else None
        description = row.get("description")
        sources.append(Source(
            title.strip(), url, description.strip() if isinstance(description, str) else "",
            tuple(value.strip() for value in highlights if isinstance(value, str) and value.strip())
            if isinstance(highlights, list) else (),
        ))
    if rows and not valid_rows:
        raise ResearchError("You.com returned malformed web results.")
    return sources


def search(query: str, api_key: str) -> list[Source]:
    if not api_key.strip():
        raise ResearchError("Set YOU_API_KEY in the .env file to enable live research.")
    try:
        response = requests.post(
            SEARCH_URL,
            headers={"X-API-Key": api_key},
            json={"query": query, "count": 10, "extraction": {"extraction_mode": "highlights"}},
            timeout=(5, 18),
            allow_redirects=False,
        )
    except requests.Timeout:
        raise ResearchError("You.com timed out. Try searching again in a moment.") from None
    except requests.RequestException:
        raise ResearchError("Could not connect to You.com. Check your internet connection and try again.") from None

    messages = {
        401: "You.com rejected the API key. Check YOU_API_KEY in your .env file.",
        402: "Your You.com account needs available API credits.",
        403: "You.com denied access. Check the API key and account permissions.",
        429: "You.com rate-limited the search. Wait a moment and retry.",
    }
    if response.status_code != 200:
        raise ResearchError(messages.get(response.status_code, f"You.com search failed (HTTP {response.status_code})."))
    try:
        payload = response.json()
    except ValueError:
        raise ResearchError("You.com returned invalid JSON. Try again in a moment.") from None
    return parse_search(payload)


def research(queries: tuple[str, ...], api_key: str) -> tuple[list[Source], list[str]]:
    sources, errors = [], []
    successes = 0
    with ThreadPoolExecutor(max_workers=len(queries)) as executor:
        futures = [executor.submit(search, query, api_key) for query in queries]
        for future in futures:
            try:
                sources.extend(future.result())
                successes += 1
            except ResearchError as error:
                if str(error) not in errors:
                    errors.append(str(error))
    if not successes:
        raise ResearchError(" ".join(errors))
    return sources, errors
