import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from streamlit.testing.v1 import AppTest

from services.scheme_matcher import INELIGIBLE, LIKELY, POSSIBLE, discover, evaluate, filter_schemes
from services.you_api import ResearchError, parse_search, search
from utils.helpers import Profile, search_queries


PROFILE = Profile(23, "Maharashtra", "Student", "Undergraduate", 200000, "OBC", None, "Scholarships")
URL = "https://benefits.maharashtra.gov.in/education/test"
PAYLOAD = {"results": {"web": [{
    "title": "Example Education Scholarship",
    "url": URL,
    "description": "Representative test fixture.",
    "contents": {"highlights": [
        "## Eligibility\n- Applicants must be a resident of Maharashtra.\n"
        "- Annual family income must not exceed ₹2,00,000.\n## Benefits\n- Fee support."
    ]},
}]}}


class ResearchTests(unittest.TestCase):
    def test_official_web_results_and_filters(self):
        unofficial = {"title": "Unofficial scheme", "url": "https://example.gov.in.invalid/test"}
        sources = parse_search({"results": {"web": [*PAYLOAD["results"]["web"], unofficial]}})
        schemes = discover(sources + sources, PROFILE)
        self.assertEqual(len(schemes), 1)
        self.assertEqual(schemes[0].sources[0].url, URL)
        self.assertIsNone(schemes[0].application_url)
        self.assertEqual(schemes[0].fields["benefits"], ["Fee support."])
        self.assertEqual(filter_schemes(schemes, "Likely Eligible"), schemes)
        self.assertEqual(filter_schemes(schemes, "State Government"), schemes)
        self.assertEqual(filter_schemes(schemes, "Central Government"), [])

    def test_empty_and_malformed_responses(self):
        self.assertEqual(parse_search({"results": {"web": []}}), [])
        with self.assertRaises(ResearchError):
            parse_search({"results": {"web": "invalid"}})

    def test_application_button_uses_retrieved_scheme_url(self):
        application_url = "https://benefits.maharashtra.gov.in/education/test/apply-online"
        application = {
            "title": "Example Education Scholarship - Apply Online",
            "url": application_url,
            "description": "Representative application page fixture.",
        }
        sources = parse_search({"results": {"web": [*PAYLOAD["results"]["web"], application]}})
        self.assertEqual(discover(sources, PROFILE)[0].application_url, application_url)

    def test_portal_heading_supplies_name_when_page_title_is_generic(self):
        payload = {"results": {"web": [{
            "title": "SchemeData",
            "url": "https://mahadbt.maharashtra.gov.in/SchemeData/SchemeData?str=test",
            "contents": {"highlights": [
                "# Example Post Matric Scholarship\n### Department Name\nExample Department\n"
                "### Eligibility\n1) Student should be resident of Maharashtra.\n"
                "2) Academic marks must be verified.\n### Documents Required\nMarks sheet."
            ]},
        }]}}
        scheme = discover(parse_search(payload), PROFILE)[0]
        self.assertEqual(scheme.name, "Example Post Matric Scholarship")
        self.assertIn("Example Department", scheme.department)
        self.assertEqual(scheme.status, POSSIBLE)
        self.assertTrue(scheme.reasons)

    @patch("services.you_api.requests.post")
    def test_live_request_contract_and_invalid_key(self, post):
        post.return_value = Mock(status_code=200, json=lambda: PAYLOAD)
        self.assertEqual(search("eligibility", "test-key")[0].url, URL)
        self.assertEqual(post.call_args.args[0], "https://ydc-index.io/v1/search")
        self.assertEqual(post.call_args.kwargs["headers"], {"X-API-Key": "test-key"})
        self.assertEqual(post.call_args.kwargs["json"]["query"], "eligibility")
        post.return_value.status_code = 401
        with self.assertRaisesRegex(ResearchError, "rejected the API key"):
            search("eligibility", "invalid")

    def test_income_matching_and_missing_information(self):
        without_income = Profile(23, "Maharashtra", "Student", "Undergraduate", None, "OBC", None, "Scholarships")
        rule = ["Annual family income must not exceed ₹2,00,000."]
        self.assertEqual(evaluate(PROFILE, rule, True)[0], LIKELY)
        self.assertEqual(evaluate(without_income, rule, True)[0], POSSIBLE)
        self.assertEqual(evaluate(PROFILE, [], False)[0], POSSIBLE)
        self.assertEqual(evaluate(PROFILE, ["Applicants must be a resident of Kerala."], True)[0], INELIGIBLE)
        self.assertEqual(len(search_queries(PROFILE)), 3)

    @patch("services.you_api.requests.post")
    def test_streamlit_sample_submit_and_filter(self, post):
        post.return_value = Mock(status_code=200, json=lambda: PAYLOAD)
        with patch.dict("os.environ", {"YOU_API_KEY": "test-key"}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.number_input(key="age").value, 18)
            app.button[0].click().run()
            self.assertEqual(app.number_input(key="age").value, 23)
            self.assertEqual(app.number_input(key="income").value, 200000)
            self.assertEqual(app.selectbox(key="category").value, "OBC")
            app.button[1].click().run()
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertEqual(app.metric[0].value, "1")
            self.assertEqual(post.call_count, 3)
            app.selectbox(key="result_filter").set_value("Central Government").run()
            self.assertFalse(app.exception)
            self.assertEqual(post.call_count, 3)
            self.assertTrue(any("No results match" in info.value for info in app.info))
