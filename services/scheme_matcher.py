import re
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import urlsplit

from services.you_api import Source
from utils.helpers import Profile, STATES, official_host


LIKELY = "Likely Eligible"
POSSIBLE = "Possibly Eligible – More Information Needed"
INELIGIBLE = "Not Eligible Based on Known Criteria"
UNKNOWN = "Not confirmed from available sources."
FILTERS = ("All Schemes", "Likely Eligible", "Possibly Eligible", "Central Government", "State Government")
SECTIONS = {
    "eligibility": "eligibility", "eligibility criteria": "eligibility", "who can apply": "eligibility",
    "benefits": "benefits", "benefit": "benefits", "scholarship amount": "benefits",
    "documents required": "documents", "required documents": "documents",
    "documents": "documents", "application deadline": "deadline",
    "last date to apply": "deadline", "deadline": "deadline",
    "department name": "department", "ministry": "department", "implementing agency": "department",
    "overview": "description", "details": "description",
}
SCHEME_WORDS = r"scholarship|scheme|fellowship|stipend|financial assistance|fee reimbursement|tuition fee|freeship|yojana|subsidy|training programme|abhiyan|pension|mission|beti bachao beti padhao|kisan samman nidhi"
RULES = (
    ("state", r"(?:must|should) be (?:a )?(?:resident|domiciled resident) of (.+)"),
    ("occupation", r"must be (?:an? )?(student|farmer|unemployed|employed|self-employed)"),
    ("education", r"must be (?:an? )?(undergraduate|postgraduate|diploma|class 10|class 12)(?: student)?"),
    ("category", r"(?:must|should) belong to (?:the )?(general|obc|sc|st|ews)(?: category)?"),
    ("age", r"must be (?:aged )?(?:between )?(\d{1,3}) (?:to|and|–|-) (\d{1,3}) years(?: old)?"),
    ("income", r"(?:the )?(?:annual family income|family annual income) (?:must|should) (?:not exceed|be at most) (?:₹|rs\.?|inr)\s*(\d[\d,]*(?:\.\d+)?)(?:\s+(lakhs?))?"),
)


@dataclass(frozen=True)
class Scheme:
    name: str
    category: str
    scope: str
    department: str
    description: str
    fields: dict[str, list[str]]
    status: str
    reasons: list[str]
    missing: list[str]
    sources: tuple[Source, ...]
    application_url: str | None


def read_evidence(source: Source) -> tuple[dict[str, list[str]], bool]:
    fields: dict[str, list[str]] = {}
    bounded = False
    for highlight in (*source.highlights, source.description):
        section = None
        structured_eligibility = False
        section_has_content = False
        for raw_line in highlight.splitlines():
            line = re.sub(r"[*#]", "", raw_line).strip()
            label, _, rest = line.partition(":")
            heading = raw_line.lstrip().startswith("#")
            label = label.strip().casefold()
            if label in SECTIONS or heading:
                bounded |= structured_eligibility and section_has_content
                section = SECTIONS.get(label)
                structured_eligibility = heading and section == "eligibility"
                section_has_content = False
                line = rest.strip()
            if section and line:
                entry = re.sub(r"^(?:[-•]|\d+[.)])\s+", "", line)
                section_has_content = True
                values = fields.setdefault(section, [])
                if entry not in values:
                    values.append(entry)
    return fields, bounded


def evaluate(profile: Profile, criteria: list[str], bounded: bool) -> tuple[str, list[str], list[str]]:
    reasons, conflicts, missing = [], [], []
    ambiguity = r"\b(?:or|either|exemption|exception|relaxation|waiver)\b"
    ambiguous = False
    for criterion in criteria:
        clause = re.sub(r"^(?:the )?(?:applicants?|candidates?|students?) ", "", criterion.rstrip(".").casefold())
        clause = " ".join(clause.replace("less than or equal to", "at most").split())
        uncertain = bool(re.search(ambiguity, clause))
        ambiguous |= uncertain
        for field, pattern in RULES:
            match = re.fullmatch(pattern, clause)
            if not match or uncertain:
                continue
            actual = getattr(profile, field)
            if field == "state" and match[1] not in {state.casefold() for state in STATES}:
                continue
            if actual is None or actual in ("Prefer not to say", "Other"):
                missing.append(f"Confirm your {field} against this condition. {criterion}")
                break
            if field == "age":
                matches = int(match[1]) <= actual <= int(match[2])
            elif field == "income":
                maximum = Decimal(match[1].replace(",", ""))
                matches = actual <= maximum * (100000 if match[2] else 1)
            else:
                matches = str(actual).casefold() == match[1]
            value = f"₹{actual:,}" if field == "income" else actual
            relation = "matches" if matches else "does not meet"
            (reasons if matches else conflicts).append(f"Your {field} ({value}) {relation} this condition. {criterion}")
            break
        else:
            missing.append(f"Verify this published condition. {criterion}")
    if not bounded:
        missing.append("Confirm the full eligibility rules on the official page.")
    if not criteria:
        missing.append("The retrieved excerpts did not contain a usable eligibility section.")
    if conflicts and not ambiguous:
        return INELIGIBLE, reasons + conflicts, missing
    if conflicts:
        missing.append("Confirm whether the published alternatives or exceptions apply.")
    if reasons and not missing:
        return LIKELY, reasons, missing
    return POSSIBLE, reasons, missing


def scheme_name(source: Source) -> str | None:
    host = official_host(source.url)
    if not host:
        return None
    path = urlsplit(source.url).path.strip("/")
    title = re.split(r"\s*[|–—]\s*", source.title, maxsplit=1)[0].strip()
    if host in ("mahadbt.maharashtra.gov.in", "www.mahadbt.maharashtra.gov.in") and path.casefold().endswith("/schemedata"):
        for highlight in source.highlights:
            heading = re.search(r"(?m)^#\s+(\S[^\n]+)", highlight)
            if heading and re.search(SCHEME_WORDS, heading[1], re.I):
                return heading[1].strip().rstrip(".")
    if len(title) < 10 or not path:
        return None
    if host in ("myscheme.gov.in", "www.myscheme.gov.in"):
        return title if re.fullmatch(r"schemes/[^/]+", path) else None
    if not re.search(SCHEME_WORDS, title, re.I) or not (source.description or source.highlights):
        return None
    if re.search(r"^(?:list of|all |about us|department of|national scholarship portal|scholarships?$|(?:government |dbt )?schemes?(?:\s*/\s*programmes)?$|application form$)", title, re.I):
        return None
    return re.sub(r"\s*[-:(]?\s*\b(?:application form|apply online)\)?$", "", title, flags=re.I).strip()


def classify(source: Source, name: str, department: list[str]) -> tuple[str, str]:
    host = official_host(source.url) or ""
    state = next((state for state in STATES if state.lower().replace(" ", "") in host.split(".")), None)
    evidence = "\n".join(source.highlights)
    label = department[0] if department else ""
    if re.search(r"\bGovernment of India\b", name, re.I) or re.search(
        r"\b(?:central sector scheme|centrally administered|central government scheme)\b", name + "\n" + evidence, re.I
    ):
        return "Central", " · ".join(filter(None, ("Government of India", label)))
    if state:
        return "State", " · ".join(filter(None, (f"Government of {state}", label)))
    if re.search(r"\bstate government scheme\b", name + "\n" + evidence, re.I):
        return "State", label
    return "", label


def discover(sources: list[Source], profile: Profile | None = None, *, query: str = "") -> list[Scheme]:
    groups: dict[str, list[Source]] = {}
    for source in sources:
        name = scheme_name(source)
        if not name:
            continue
        key = re.sub(r"\W+", " ", name.casefold()).strip()
        group = groups.setdefault(key, [])
        if source.url not in {item.url for item in group}:
            group.append(source)
    results = []
    for group in groups.values():
        source = max(group, key=lambda item: sum(map(len, read_evidence(item)[0].values())))
        name = scheme_name(source) or source.title
        fields, bounded = read_evidence(source)
        if profile is None:
            status, reasons, missing = POSSIBLE, [], ["Open Eligibility Checker to compare your profile."]
        else:
            status, reasons, missing = evaluate(profile, fields.get("eligibility", []), bounded)
        scope, department = classify(source, name, fields.get("department", []))
        category = (
            "Scholarship" if re.search(r"scholarship|fellowship|stipend|freeship", name, re.I)
            else "Education" if re.search(r"education|student|fee", name, re.I)
            else "Employment" if re.search(r"employment|training|skill", name, re.I)
            else "Welfare"
        )
        # Require an application form explicitly named in a retrieved official result.
        application_url = next((
            item.url for item in group
            if re.search(r"\b(?:apply online|application form)\b", item.title, re.I)
            and re.search(r"(?:apply[-_/]online|application[-_/]form)", urlsplit(item.url).path, re.I)
        ), None)
        results.append(Scheme(
            name, category, scope, department,
            " ".join(fields.get("description", [])[:2]) or source.description or UNKNOWN,
            fields, status, reasons, missing,
            (source, *(item for item in group if item != source)), application_url,
        ))
    order = {LIKELY: 0, POSSIBLE: 1, INELIGIBLE: 2}
    query_terms = set(re.findall(r"\w+", query.casefold()))

    def rank(item: Scheme):
        name_terms = re.findall(r"\w+", item.name.casefold())
        overlap = len(query_terms.intersection(name_terms))
        exactness = overlap / len(name_terms) if name_terms else 0
        return order[item.status], -overlap, -exactness, -len(item.fields)

    return sorted(results, key=rank)[:8]


def filter_schemes(schemes: list[Scheme], selected: str) -> list[Scheme]:
    choices = {
        "Likely Eligible": ("status", LIKELY), "Possibly Eligible": ("status", POSSIBLE),
        "Central Government": ("scope", "Central"), "State Government": ("scope", "State"),
    }
    if selected not in choices:
        return schemes
    field, value = choices[selected]
    return [scheme for scheme in schemes if getattr(scheme, field) == value]
