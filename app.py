import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from services.scheme_matcher import FILTERS, INELIGIBLE, LIKELY, POSSIBLE, UNKNOWN, Scheme, discover, filter_schemes
from services.you_api import ResearchError, research
from utils.helpers import CATEGORIES, EDUCATION, GENDERS, INTERESTS, OCCUPATIONS, STATES, Profile, official_host, search_queries


load_dotenv(Path(__file__).with_name(".env"))
st.set_page_config(page_title="YojanaMitra", page_icon="🔎", layout="wide")

st.html("""
<style>
.stMainBlockContainer { max-width: 1120px; padding-top: 3rem; }
.yojanamitra-hero {
  background: radial-gradient(ellipse at 95% 110%, #08756b 0%, transparent 66%),
              linear-gradient(125deg, #102641, #173a53);
  padding: clamp(1.5rem, 5vw, 3.5rem);
  border-radius: 24px;
  box-shadow: 0 12px 30px #14294219;
  color: #fff;
  margin-bottom: .9rem;
}
.yojanamitra-hero h1 {
  color: #fff; font-size: clamp(2.5rem, 7vw, 4.8rem);
  line-height: 1.05; letter-spacing: -.065em; margin: 0 0 .65rem; padding: 0;
}
.yojanamitra-hero p { color: #e5f3f1; max-width: 38rem; margin: 0 0 .9rem; font-size: 1.05rem; }
.yojanamitra-hero .tagline { font-size: 1.25rem; font-weight: 650; color: #fff; }
.research-indicator {
  display: inline-block; background: #d6f6ec; color: #164940; border-radius: 999px;
  padding: .3rem .85rem; font-weight: 650; font-size: .82rem;
}
[data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMetric"] { border-radius: 18px; }
[data-testid="stForm"] { background: #fff; padding: 1.4rem; }
[data-testid="stMetric"] { background: #fff; padding: .85rem; }
[data-testid="stLinkButton"] a, [data-testid="stFormSubmitButton"] button { min-height: 2.8rem; }
[data-testid="stText"] { white-space: pre-wrap; overflow-wrap: anywhere; font-family: inherit; }
[data-testid="stText"] pre { white-space: inherit; font-family: inherit; }
</style>
<header class="yojanamitra-hero">
  <h1>YojanaMitra</h1>
  <p class="tagline">Your eligibility. Your opportunities. One search.</p>
  <p>Discover scholarships and government benefits you may qualify for.</p>
  <span class="research-indicator">Powered by You.com Live Research</span>
</header>
""")


def sample_profile() -> None:
    st.session_state.pop("last_search", None)
    st.session_state.pop("search_cache", None)
    st.session_state.update(
        age=23, state="Maharashtra", occupation="Student", education="Undergraduate",
        income=200000, category="OBC", gender=None, interest="Scholarships",
    )


def run_search(profile: Profile) -> None:
    queries = search_queries(profile)
    cached = st.session_state.get("search_cache")
    if cached and cached[0] == queries and time.monotonic() - cached[1] < 180:
        sources, warnings = cached[2], []
    else:
        sources, warnings = research(queries, os.getenv("YOU_API_KEY", "").strip())
        if not warnings:
            st.session_state.search_cache = (queries, time.monotonic(), sources)
    st.session_state.last_search = (discover(sources, profile), warnings)


def show_scheme(scheme: Scheme) -> None:
    colors = {LIKELY: "green", POSSIBLE: "orange", INELIGIBLE: "red"}
    with st.container(border=True):
        st.subheader(scheme.name)
        st.badge(scheme.status, color=colors[scheme.status])
        details = [scheme.category]
        details.append(f"{scheme.scope} scheme" if scheme.scope else "Government level unconfirmed")
        if scheme.department:
            details.append(scheme.department)
        st.text(" · ".join(details), width="stretch")
        st.text(scheme.description, width="stretch")
        left, right = st.columns(2)
        for column, key, label in (
            (left, "benefits", "Benefits"), (right, "deadline", "Application deadline"),
            (left, "eligibility", "Eligibility requirements"), (right, "documents", "Required documents"),
        ):
            with column:
                st.markdown(f"**{label}**")
                values = scheme.fields.get(key, [])
                st.text("\n".join(values) if values else UNKNOWN, width="stretch")
        with st.expander("Why am I matched with this scheme?"):
            for line in scheme.reasons:
                st.text(line, width="stretch")
            if scheme.missing:
                st.markdown("**Eligibility needs verification.**")
                for line in scheme.missing:
                    st.text(line, width="stretch")
        st.caption("Official-domain sources retrieved through You.com. Confirm requirements and dates on the source page.")
        for index, source in enumerate(scheme.sources, start=1):
            label = f"Source {index} · {official_host(source.url)}"
            st.link_button(label, source.url, help=source.title)
        if scheme.application_url:
            st.link_button("Apply / Visit Official Website", scheme.application_url, type="primary")
        else:
            st.link_button("View Official Details", scheme.sources[0].url)


st.header("Your profile")
for key, value in (
    ("age", 18), ("occupation", OCCUPATIONS[0]), ("education", EDUCATION[0]),
    ("category", "Prefer not to say"), ("interest", INTERESTS[0]),
):
    st.session_state.setdefault(key, value)
st.button("Try Sample Student Profile", on_click=sample_profile)
with st.form("profile"):
    first, second = st.columns(2)
    with first:
        age = st.number_input("Age", min_value=0, max_value=120, step=1, key="age")
        occupation = st.selectbox("Occupation", OCCUPATIONS, index=None, key="occupation")
        income = st.number_input("Annual family income (₹, optional)", min_value=0, value=None, step=1000, key="income")
        gender = st.selectbox("Gender (optional)", GENDERS, index=None, key="gender")
    with second:
        state = st.selectbox("State or union territory", STATES, index=None, key="state")
        education = st.selectbox("Education level", EDUCATION, index=None, key="education")
        category = st.selectbox("Category", CATEGORIES, index=None, key="category")
        interest = st.selectbox("Interest", INTERESTS, index=None, key="interest")
    submitted = st.form_submit_button("Find My Schemes", type="primary", width="stretch")

if submitted:
    st.session_state.pop("last_search", None)
    try:
        profile = Profile(age, state, occupation, education, income, category, gender, interest)
        with st.spinner("Researching government sources through You.com…"):
            run_search(profile)
    except (ValueError, ResearchError) as error:
        st.error(str(error))

if "last_search" in st.session_state:
    schemes, warnings = st.session_state.last_search
    st.header("Your scheme results")
    for warning in warnings:
        st.warning(warning)
    all_count, likely_count, possible_count = st.columns(3)
    all_count.metric("Schemes found", len(schemes))
    likely_count.metric("Likely eligible", sum(scheme.status == LIKELY for scheme in schemes))
    possible_count.metric("Need more information", sum(scheme.status == POSSIBLE for scheme in schemes))
    if schemes:
        selected = st.selectbox("Filter results", FILTERS, key="result_filter")
        visible = filter_schemes(schemes, selected)
        if not visible:
            st.info("No results match this filter.")
        for scheme in visible:
            show_scheme(scheme)
    else:
        st.info("This search returned no identifiable scheme pages from official sources. Try a broader interest or check your state’s portal.")

with st.expander("How YojanaMitra works"):
    st.markdown("""
1. We search current web information through You.com.
2. We prioritize official government sources.
3. We compare your profile with published eligibility conditions.
4. We provide official links for final verification.
    """.strip())
    st.caption("Search sends your state, interest and student education level or occupation to You.com.")
st.caption("YojanaMitra is an information discovery assistant, not an official government portal. Eligibility and deadlines must be confirmed on the relevant government website.")
