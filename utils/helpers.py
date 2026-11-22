from dataclasses import dataclass
from urllib.parse import urlsplit


STATES = (
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
    "Bihar", "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
    "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
)
OCCUPATIONS = ("Student", "Employed", "Unemployed", "Self-employed", "Farmer", "Other")
EDUCATION = ("Class 10", "Class 12", "Diploma", "Undergraduate", "Postgraduate", "Other")
CATEGORIES = ("General", "OBC", "SC", "ST", "EWS", "Prefer not to say")
INTERESTS = ("Scholarships", "Education Support", "Employment", "Skill Development", "All Schemes")
GENDERS = ("Woman", "Man", "Non-binary", "Other", "Prefer not to say")
TERMS = dict(zip(INTERESTS, (
    "scholarship", "education financial assistance", "employment assistance",
    "skill development training", "government welfare benefit",
)))


@dataclass(frozen=True)
class Profile:
    age: int
    state: str
    occupation: str
    education: str
    income: int | None
    category: str
    gender: str | None
    interest: str

    def __post_init__(self):
        if not 0 <= self.age <= 120 or (self.income is not None and self.income < 0):
            raise ValueError("Enter a valid age and a non-negative annual family income.")
        choices = (
            (self.state, STATES), (self.occupation, OCCUPATIONS),
            (self.education, EDUCATION), (self.category, CATEGORIES),
            (self.gender, (*GENDERS, None)), (self.interest, INTERESTS),
        )
        if any(value not in options for value, options in choices):
            raise ValueError("Select your profile values from the available choices.")


def search_queries(profile: Profile) -> tuple[str, ...]:
    term = TERMS[profile.interest]
    audience = profile.education if profile.occupation == "Student" else profile.occupation
    state_site = (
        "site:mahadbt.maharashtra.gov.in" if profile.state == "Maharashtra"
        and profile.interest in ("Scholarships", "Education Support") else "site:gov.in"
    )
    state_audience = "post matric" if state_site.startswith("site:mahadbt") and profile.education in (
        "Diploma", "Undergraduate", "Postgraduate",
    ) else audience
    central_site = "site:scholarships.gov.in" if profile.interest == "Scholarships" else "site:myscheme.gov.in"
    queries = (
        f'{state_site} "{profile.state}" {state_audience} {term} scheme eligibility benefits documents',
        f'{central_site} India {audience} {term} scheme eligibility benefits application',
    )
    if profile.interest == "Scholarships":
        return (*queries, f'site:myscheme.gov.in/schemes {profile.state} {audience} scholarship eligibility')
    return queries


def official_host(url: str) -> str | None:
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        if parts.scheme != "https" or parts.username or parts.password or parts.port not in (None, 443):
            return None
        if host.split(".", 1)[0] in ("dev", "staging", "test", "uat"):
            return None
    except ValueError:
        return None
    if host in ("gov.in", "nic.in", "aicte-india.org") or host.endswith(
        (".gov.in", ".nic.in", ".aicte-india.org")
    ):
        return host
    return None
