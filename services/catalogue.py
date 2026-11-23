"""Persistent catalogue and focused discovery plans for the government portals."""
import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from utils.helpers import STATES

CATEGORY_TOPICS = {
    "Students": (
        ("Scholarship", "myscheme.gov.in", "student scholarship"),
        ("Scholarship", "scholarships.gov.in", "scholarship guidelines eligibility"),
        ("Education support", "mahadbt.maharashtra.gov.in/SchemeData", "student tuition fee freeship"),
        ("Education support", "web.umang.gov.in/landing/scheme/detail", "education loan students"),
        ("Skills", "india.gov.in", "student skill training scheme"),
        ("Scholarship", "gov.in", "state student scholarship eligibility benefits"),
    ),
    "Women": (
        ("Maternity", "myscheme.gov.in", "maternity benefit pregnant women"),
        ("Entrepreneurship", "myscheme.gov.in", "women entrepreneur subsidy loan"),
        ("Financial assistance", "web.umang.gov.in/landing/scheme/detail", "women financial assistance scheme"),
        ("Maternity", "wcd.gov.in", "maternity nutrition scheme eligibility"),
        ("Entrepreneurship", "gov.in", "state women entrepreneurship assistance scheme eligibility"),
        ("Education support", "india.gov.in", "women girls education assistance scheme"),
    ),
    "Farmers": (
        ("Income support", "myscheme.gov.in", "farmer income support"),
        ("Crop insurance", "myscheme.gov.in", "farmer crop insurance"),
        ("Equipment and irrigation", "myscheme.gov.in", "farmer irrigation farm equipment subsidy"),
        ("Income support", "pmkisan.gov.in", "PM Kisan scheme farmer eligibility"),
        ("Crop insurance", "gov.in", "crop insurance farmer scheme eligibility"),
        ("Equipment and irrigation", "gov.in", "PM KUSUM solar pump scheme farmer eligibility"),
        ("Equipment and irrigation", "gov.in", "micro irrigation per drop more crop subsidy farmers scheme"),
        ("Income support", "india.gov.in", "farmer assistance welfare scheme eligibility benefits"),
        ("Income support", "gov.in", "state farmer pension subsidy scheme eligibility beneficiaries"),
        ("Equipment and irrigation", "web.umang.gov.in/landing/scheme/detail", "farmer agriculture equipment subsidy"),
    ),
}
TOPICS = {
    "Scholarship": r"scholarship|fellowship|freeship|stipend",
    "Education support": r"education|tuition|student|school|college|girls",
    "Skills": r"skill|training|apprentice",
    "Maternity": r"maternity|pregnan|maternal|janani|vandana",
    "Entrepreneurship": r"entrepreneur|business|enterprise|self.employ",
    "Financial assistance": r"financial|assistance|pension|welfare|subsid|loan",
    "Income support": r"income|kisan|farmer|farmland",
    "Crop insurance": r"insurance|fasal|crop",
    "Equipment and irrigation": r"equipment|irrigation|pump|mechanization|machinery",
}
AUDIENCES = {
    "Students": r"student|scholarship|fellowship|education|tuition|school|college|freeship|apprentice",
    "Women": r"\bwom[ae]n\b|women|female|girl|maternity|pregnan|maternal|janani|vandana|widow|mahila",
    "Farmers": r"farmer|agricultur|kisan|horticultur|crop|irrigation|cultivat",
}
DB = Path(os.environ.get("YOJANAMITRA_DB", Path(__file__).resolve().parents[1] / ".yojanamitra.sqlite3"))
LOCKS = {category: threading.Lock() for category in CATEGORY_TOPICS}


@contextmanager
def connection():
    db = sqlite3.connect(DB, timeout=15)
    try:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS schemes (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, state TEXT, scope TEXT,
                department TEXT, official_info_url TEXT NOT NULL,
                official_application_url TEXT, last_verified TEXT NOT NULL,
                verification_status TEXT NOT NULL, record TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS categories (
                scheme_id TEXT NOT NULL REFERENCES schemes(id), category TEXT NOT NULL,
                benefit TEXT NOT NULL, PRIMARY KEY (scheme_id, category, benefit)
            );
            CREATE INDEX IF NOT EXISTS catalogue_category ON categories(category, benefit);
            CREATE TABLE IF NOT EXISTS refreshes (category TEXT PRIMARY KEY, refreshed REAL NOT NULL);
        """)
        with db:
            yield db
    finally:
        db.close()


def state_for(item):
    if item["scope"] == "Central":
        return ""
    hostname = urlsplit(item["sources"][0]["url"]).hostname or ""
    candidates = [state for state in STATES if state.casefold().replace(" ", "") in hostname.split(".")]
    if not candidates and item["scope"] == "State":
        label = item["department"]
        candidates = [state for state in STATES if re.search(r"\b" + re.escape(state) + r"\b", label, re.I)]
    if not candidates:
        description = item["description"]
        name = item["name"]
        candidates = [state for state in STATES if re.search(
            r"\b(?:government of\s+" + re.escape(state) + r"|" + re.escape(state) + r"\s+government)\b",
            description, re.I) or re.search(r"[-–:]\s*" + re.escape(state) + r"$", name, re.I)]
    return max(candidates, key=len, default="")


def save(schemes, category=None):
    items = []
    with connection() as db:
        for scheme in schemes:
            item = asdict(scheme)
            item["sources"] = [{"title": source.title, "url": source.url} for source in scheme.sources]
            state = state_for(item)
            name = re.sub(r"\b(?:the|scheme|yojana)\b", "", item["name"].casefold())
            key = re.sub(r"\W+", " ", name).strip() + "|" + state
            scheme_id = hashlib.sha256(key.encode()).hexdigest()[:20]
            if state and not item["scope"]:
                item["scope"] = "State"
            existing = db.execute("SELECT id FROM schemes WHERE official_info_url=?",
                                  (item["sources"][0]["url"],)).fetchone()
            if existing:
                scheme_id = existing[0]
            stamp = datetime.now(timezone.utc).date().isoformat()
            current = db.execute("SELECT record FROM schemes WHERE id=?", (scheme_id,)).fetchone()
            if current:
                previous = json.loads(current[0])
                if previous["verification_status"] == "Official details retrieved":
                    item["fields"] = {**item["fields"], **previous["fields"]}
                    item["objectives"] = previous.get("objectives", [])
                else:
                    item["fields"] = {**previous["fields"], **item["fields"]}
                item["application_url"] = item["application_url"] or previous["application_url"]
                item["sources"] += [source for source in previous["sources"] if source["url"] not in {s["url"] for s in item["sources"]}]
            status = previous["verification_status"] if current else "Official source identified"
            item.update(id=scheme_id, state=state, last_verified=stamp, verification_status=status)
            item["eligibility_rules"] = [{"condition": clause, "source": item["sources"][0]["url"]}
                                         for clause in item["fields"].get("eligibility", [])]
            db.execute("INSERT OR REPLACE INTO schemes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                scheme_id, item["name"], state, item["scope"], item["department"], item["sources"][0]["url"],
                item["application_url"], stamp, item["verification_status"], json.dumps(item, ensure_ascii=False),
            ))
            if category:
                evidence = item["name"] + " " + item["description"]
                benefits = {label for label, _, _ in CATEGORY_TOPICS[category] if re.search(TOPICS[label], evidence, re.I)} or {"Other"}
                db.executemany("INSERT OR IGNORE INTO categories VALUES (?, ?, ?)", [(scheme_id, category, label) for label in benefits])
            items.append(item)
    return items


def get(scheme_id):
    with connection() as db:
        row = db.execute("SELECT record FROM schemes WHERE id=?", (scheme_id,)).fetchone()
    return json.loads(row[0]) if row else None


def list_schemes(category=None, state="", scope="", benefit="", query="", page=1, size=12):
    with connection() as db:
        rows = db.execute("""
            SELECT s.record FROM schemes s
            WHERE (?='' OR s.state=?) AND (?='' OR s.scope=?)
              AND (?='' OR EXISTS(SELECT 1 FROM categories c WHERE c.scheme_id=s.id AND c.category=? AND (?='' OR c.benefit=?)))
            ORDER BY s.name, s.id
        """, (state, state, scope, scope, category or "", category or "", benefit, benefit)).fetchall()
    terms = set(re.findall(r"\w+", query.casefold())) - {"for", "the", "a", "schemes", "scheme", "in", "show", "me"}
    records = [json.loads(row[0]) for row in rows]
    if terms:
        records = [item for item in records if all(term in (item["name"] + " " + item["description"]).casefold() for term in terms)]
        records.sort(key=lambda item: (query.casefold() not in item["name"].casefold(), item["name"]))
    offset = (page - 1) * size
    return {"schemes": records[offset:offset + size], "total": len(records), "page": page, "has_more": offset + size < len(records), "warnings": []}


def fresh(category):
    with connection() as db:
        row = db.execute("SELECT refreshed FROM refreshes WHERE category=?", (category,)).fetchone()
    return bool(row and time.time() - row[0] < 21600)


def mark_refreshed(category):
    with connection() as db:
        db.execute("INSERT OR REPLACE INTO refreshes VALUES (?, ?)", (category, time.time()))


def enrich(scheme_id, details):
    with connection() as db:
        row = db.execute("SELECT record FROM schemes WHERE id=?", (scheme_id,)).fetchone()
        if not row:
            return
        item = json.loads(row[0])
        sections = details["sections"]
        item["fields"].update({key: value for key, value in sections.items() if value})
        if sections.get("overview"):
            item["objectives"] = sections["overview"]
        if sections.get("eligibility"):
            # Keep provisional status when source completeness cannot be proven.
            item["eligibility_rules"] = [{"condition": clause, "source": details["sources"][-1]["url"]}
                                         for clause in sections["eligibility"]]
        item["application_url"] = details["application_url"] or item["application_url"]
        item["last_verified"] = datetime.now(timezone.utc).date().isoformat()
        item["verification_status"] = "Official details retrieved"
        db.execute("""UPDATE schemes SET official_application_url=?, last_verified=?,
                   verification_status=?, record=? WHERE id=?""",
                   (item["application_url"], item["last_verified"], item["verification_status"],
                    json.dumps(item, ensure_ascii=False), scheme_id))


def normalize_existing_states():
    with connection() as db:
        for scheme_id, encoded in db.execute("SELECT id, record FROM schemes WHERE state=''").fetchall():
            item = json.loads(encoded)
            state = state_for(item)
            if state:
                item.update(state=state, scope=item["scope"] or "State")
                db.execute("UPDATE schemes SET state=?, scope=?, record=? WHERE id=?",
                           (state, item["scope"], json.dumps(item, ensure_ascii=False), scheme_id))
