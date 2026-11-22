"""Serve the React build and expose the existing You.com research service locally."""

import argparse
import json
import os
import re
import time
from dataclasses import asdict
from difflib import get_close_matches
from functools import lru_cache, partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv

from services.scheme_details import extract_page, myscheme_page, parse_details
from services.scheme_matcher import discover, read_evidence, scheme_name
from services.you_api import ResearchError, Source, research
from utils.helpers import CATEGORIES, EDUCATION, GENDERS, INTERESTS, OCCUPATIONS, STATES, Profile, official_host, search_queries


ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
FEATURED_TOPICS = (
    ("Prime Minister Scholarship Scheme", {"scholarship"}),
    ("Beti Bachao Beti Padhao", {"beti", "bachao", "padhao"}),
    ("PM Kisan Samman Nidhi", {"kisan", "samman", "nidhi"}),
)
DOCUMENT_TOPIC = re.compile(
    r"^(?:(?:what|which) documents (?:are )?(?:required|needed)|documents required|required documents|documents)"
    r"\s+(?:to apply for|for)\s+(.+?)\??$", re.I,
)
SHAHU = Source(
    "Rajarshi Chhatrapati Shahu Maharaj Education Fee Scholarship Scheme",
    "https://dte.maharashtra.gov.in/rajarshi-chhatrapati-shahu-maharaj/",
    "Maharashtra Directorate of Technical Education scholarship for eligible technical education students.",
    (),
)
SHAHU_PORTAL = (
    "https://mahadbt.maharashtra.gov.in/SchemeData/SchemeData?"
    "str=E9DDFA703C38E51A7F4D327BDEB7125DE0BA4AE1C51180C272281017EBEF6F7C"
)
SHAHU_NAMES = {
    "rajashri shau maharaj shikshan shulk yojana",
    "rajarshi chhatrapati shahu maharaj shikshan shulkh shishyavrutti yojna",
    "rajarshi shahu maharaj shikshan shulk yojana",
    "rajarshi chhatrapati shahu maharaj",
    "rajarshi chhatrapati shahu maharaj scholarship",
    "rajarshi chhatrapati shahu maharaj education fee scholarship scheme",
}
STUDENT_SCHEME = re.compile(
    r"\b(?:scholarships?|fellowships?|students?|education|tuition|freeship|"
    r"stipends?|skill loans?|apprenticeship|school|college|hostel)\b", re.I,
)
ARTICLE_PATH = re.compile(
    r"(?:^|[/_-])(?:news|blog|articles?|press[-_]?releases?|media|announcements?|"
    r"notifications?|circulars?|downloads?)(?:[/_.-]|$)", re.I,
)
ARTICLE_TITLE = re.compile(
    r"\b(?:approves?|announces?|launches?|press release|news update|explained|"
    r"everything you need to know|how to apply)\b", re.I,
)
BROAD_SEARCH = re.compile(
    r"^(?:scholarships?|women empowerment|farmer subsidy|startup support|maternity benefit|"
    r"government schemes\b.*)$|\b(?:schemes? for|scholarships? for|benefits? for|"
    r"loans? for|subsid(?:y|ies) for|how (?:do|can)|looking for)\b", re.I,
)


def name_words(value: str) -> list[str]:
    return re.findall(r"[^\W_]+", value.casefold())


def shahu_lookup(query: str) -> bool:
    return " ".join(name_words(query)) in SHAHU_NAMES or query.rstrip("/") == SHAHU.url.rstrip("/")


def close_scheme_name(query: str, title: str) -> bool:
    terms, words = name_words(query), name_words(title)
    if len(terms) < 3:
        return False
    matched = []
    for term in terms:
        options = [word for word in words if word not in matched]
        choice = [term] if term in options else get_close_matches(term, options, n=1, cutoff=0.82) if len(term) >= 4 else []
        if not choice:
            return False
        matched.extend(choice)
    return len(set(terms) & set(words)) >= 2


def is_scheme_page(source: Source) -> bool:
    url = urlsplit(source.url)
    path = url.path.rstrip("/")
    host = url.hostname or ""
    if host.removeprefix("www.") in {"pib.gov.in", "pib.nic.in", "ddnews.gov.in", "newsonair.gov.in"}:
        return False
    if ARTICLE_PATH.search(path) or ARTICLE_TITLE.search(source.title) or path.lower().endswith(".pdf"):
        return False
    if not scheme_name(source):
        return False
    if re.search(r"/(?:schemes/[^/]+|schemedata|scheme/detail/[^/]+)$", path, re.I):
        return True
    fields, _ = read_evidence(source)
    return bool(fields.keys() & {"eligibility", "benefits", "documents"})


def search_candidates(sources: list[Source], query: str, category: str | None):
    if shahu_lookup(query):
        official = next((source for source in sources if source.url.rstrip("/") == SHAHU.url.rstrip("/")), SHAHU)
        return discover([Source(SHAHU.title, SHAHU.url, SHAHU.description, official.highlights)])
    pages = [source for source in sources if is_scheme_page(source)]
    if category == "Students":
        pages = [source for source in pages if STUDENT_SCHEME.search(scheme_name(source) or "")]
    elif not category and not BROAD_SEARCH.search(query):
        terms = set(name_words(query))
        matches = [source for source in pages if terms and terms.issubset(name_words(scheme_name(source) or ""))]
        exact = [source for source in matches if name_words(scheme_name(source) or "") == name_words(query)]
        if exact or matches:
            return discover(exact or matches, query=query)[:1]
        close = discover([source for source in pages if close_scheme_name(query, scheme_name(source) or "")], query=query)
        return close if len(close) == 1 else []
    return discover(pages, query=query)


@lru_cache(maxsize=2)
def featured_sources(three_minute_window: int, api_key: str):
    queries = tuple(f"site:gov.in {topic} government scheme eligibility benefits" for topic, _ in FEATURED_TOPICS)
    return research(queries, api_key)


def detailed_scheme(body, api_key):
    name, url = body.get("query"), body.get("source")
    if not isinstance(name, str) or not 2 <= len(name) <= 300:
        raise ValueError("Invalid scheme name.")
    if url is not None and (not isinstance(url, str) or not official_host(url)):
        raise ValueError("Invalid official source.")
    is_shahu = shahu_lookup(name)
    if is_shahu:
        urls = [SHAHU_PORTAL, SHAHU.url]
    elif url and myscheme_page(url):
        urls = [url]
    else:
        # Compare names before using a catalog hit to avoid conflating similar schemes.
        try:
            hits, _ = research((f"site:myscheme.gov.in/schemes {name}",), api_key)
        except ResearchError:
            hits = []
        identity = set(name_words(name)) - {"scheme", "the"}
        match = next((hit for hit in hits if myscheme_page(hit.url)
                      and set(name_words(scheme_name(hit) or "")) - {"scheme", "the"} == identity), None)
        if match:
            urls = [match.url, url]
        else:
            urls = [url]

    details = {"sections": {}, "tables": [], "sources": [], "application_url": None}
    for address in dict.fromkeys(filter(None, urls)):
        try:
            markdown = extract_page(address, api_key, int(time.time() // 21600))
            sections, tables, application = parse_details(markdown)
        except (ValueError, KeyError, TypeError, requests.RequestException):
            continue
        if not sections and not tables:
            continue
        # The administering department takes precedence on overlapping fields.
        details["sections"].update(sections)
        if tables:
            table_sections = {table["section"] for table in tables}
            details["tables"] = [table for table in details["tables"] if table["section"] not in table_sections] + tables
        details["application_url"] = application or details["application_url"]
        details["sources"].append({"title": "myScheme" if myscheme_page(address) else "Official department source", "url": address})

    if is_shahu:
        if any(item["url"] == SHAHU_PORTAL for item in details["sources"]):
            details["sections"].setdefault("audience", [
                "Maharashtra students in eligible diploma, degree, or postgraduate technical and professional courses admitted through the Centralized Admission Process (CAP)."
            ])
        details["sections"].setdefault("timing", [
            "The MahaDBT notice directs fresh and renewal applications for academic year 2026–27 to MahaDBT 2.0. Check the scheme listing for earlier cycles and closing dates."
        ])
        details["application_url"] = "https://mahadbt2.maharashtra.gov.in/"
        details["portal_url"] = SHAHU_PORTAL
    return {"schemes": [], "warnings": [], "details": details}


def run_research(body: dict) -> dict:
    mode = body.get("mode")
    api_key = os.getenv("YOU_API_KEY", "").strip()
    if mode == "details":
        return detailed_scheme(body, api_key)
    profile = None
    query = ""
    topic_terms = set()
    category = body.get("category")
    if category not in ("Students", "Women", "Farmers", None):
        raise ValueError("Unknown scheme category.")
    if mode == "featured":
        sources, warnings = featured_sources(int(time.monotonic() // 180), api_key)
        featured = []
        for topic, terms in FEATURED_TOPICS:
            matches = discover(sources, query=topic)
            match = next((item for item in matches if terms.issubset(re.findall(r"\w+", item.name.casefold()))), None)
            if match:
                featured.append(match)
        candidates = featured
    else:
        if mode == "eligibility":
            profile = Profile(**body.get("profile", {}))
            queries = search_queries(profile)
        elif mode in ("search", "chat"):
            query = body.get("query")
            if not isinstance(query, str) or not 2 <= len(query.strip()) <= 300:
                raise ValueError("Enter a search between 2 and 300 characters.")
            query = " ".join(query.split())
            document_topic = DOCUMENT_TOPIC.fullmatch(query) if mode == "chat" else None
            if document_topic:
                query = document_topic[1]
                topic_terms = {term for term in re.findall(r"\w+", query.casefold()) if len(term) > 2}
            queries = (
                f"site:myscheme.gov.in/schemes India government scheme {query}",
                f"site:gov.in India government scheme {query}",
            )
            if category == "Students":
                queries = (
                    "site:myscheme.gov.in/schemes student scholarship education fee eligibility",
                    "site:mahadbt.maharashtra.gov.in/SchemeData student scholarship freeship eligibility",
                    "site:web.umang.gov.in/landing/scheme/detail student scholarship education loan eligibility",
                )
            elif mode == "search" and shahu_lookup(query):
                queries = (f'site:dte.maharashtra.gov.in "Rajarshi Chhatrapati Shahu Maharaj" scholarship',)
        else:
            raise ValueError("Unknown research mode.")
        try:
            sources, warnings = research(queries, api_key)
        except ResearchError as error:
            if mode != "search" or not shahu_lookup(query):
                raise
            sources, warnings = [], [str(error)]
        candidates = search_candidates(sources, query, category) if mode == "search" else discover(sources, profile, query=query)

    schemes = []
    for scheme in candidates:
        if topic_terms and not topic_terms.issubset(re.findall(r"\w+", scheme.name.casefold())):
            continue
        item = asdict(scheme)
        item["sources"] = [{"title": source.title, "url": source.url} for source in scheme.sources]
        schemes.append(item)
    return {"schemes": schemes, "warnings": warnings}


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path == "/api/options":
            self.send_json(200, dict(state=STATES, occupation=OCCUPATIONS, education=EDUCATION,
                                     category=CATEGORIES, gender=GENDERS, interest=INTERESTS))
            return
        super().do_GET()

    def list_directory(self, path):
        self.send_error(404)
        return None

    def send_json(self, status, payload):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self):
        if urlsplit(self.path).path != "/api/research":
            self.send_json(404, {"error": "Unknown endpoint."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 8192:
                raise ValueError("Invalid request length.")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Expected a JSON request.")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object.")
            self.send_json(200, run_research(body))
        except (TypeError, ValueError, UnicodeDecodeError):
            self.send_json(400, {"error": "Check the profile or search text and try again."})
        except ResearchError as error:
            self.send_json(503, {"error": str(error)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8502)
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=DIST)) as server:
        print(f"YojanaSetu is running at http://127.0.0.1:{args.port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
