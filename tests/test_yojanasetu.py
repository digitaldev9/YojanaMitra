import unittest
from unittest.mock import patch

from services.scheme_details import parse_details
from services.you_api import Source
from yojanasetu_server import run_research


SOURCES = [
    Source("Example Rural Benefit Scheme", "https://example.gov.in/schemes/rural", "Rural support.",
           ("## Documents Required\n- Residence proof",)),
    Source("Example Education Benefit Scheme", "https://example.gov.in/schemes/education", "Education support.",
           ("## Documents Required\n- Enrollment proof",)),
]


class ReactResearchTests(unittest.TestCase):
    @patch("yojanasetu_server.research", return_value=(SOURCES, []))
    def test_scheme_search_ranks_named_scheme_and_does_not_send_raw_highlights(self, research):
        result = run_research({"mode": "search", "query": "Example Education Benefit"})
        self.assertEqual(len(result["schemes"]), 1)
        first = result["schemes"][0]
        self.assertEqual(first["name"], "Example Education Benefit Scheme")
        self.assertEqual(first["sources"], [{"title": SOURCES[1].title, "url": SOURCES[1].url}])
        self.assertEqual(len(research.call_args.args[0]), 2)

    @patch("yojanasetu_server.research", return_value=(SOURCES, []))
    def test_named_document_question_excludes_unrelated_schemes(self, research):
        result = run_research({"mode": "chat", "query": "Documents required for Example Education Benefit"})
        self.assertEqual([item["name"] for item in result["schemes"]], [SOURCES[1].title])
        self.assertEqual(result["schemes"][0]["fields"]["documents"], ["Enrollment proof"])
        self.assertNotIn("Documents required", research.call_args.args[0][0])

    def test_rejects_empty_search(self):
        with self.assertRaises(ValueError):
            run_research({"mode": "search", "query": " "})

    @patch("yojanasetu_server.research", return_value=(SOURCES, []))
    def test_shahu_search_returns_only_the_official_dte_page(self, research):
        result = run_research({"mode": "search", "query": "rajashri shau maharaj shikshan shulk yojana"})
        self.assertEqual([item["sources"][0]["url"] for item in result["schemes"]],
                         ["https://dte.maharashtra.gov.in/rajarshi-chhatrapati-shahu-maharaj/"])

    @patch("yojanasetu_server.research")
    def test_students_excludes_press_releases_and_non_student_schemes(self, research):
        article = Source("Cabinet approves Example Education Scholarship Scheme",
                         "https://pib.gov.in/PressRelease.aspx", "", ("## Eligibility\nStudents",))
        research.return_value = ([*SOURCES, article], [])
        result = run_research({"mode": "search", "query": "student scholarships", "category": "Students"})
        self.assertEqual([item["name"] for item in result["schemes"]], [SOURCES[1].title])


class SchemeDetailsTests(unittest.TestCase):
    def test_extracts_tables_steps_and_official_application(self):
        sections, tables, application = parse_details(
            "## Benefits\n| Course | Fee |\n| --- | --- |\n| Diploma | 50% |\n"
            "## How to apply\n1. [Apply online](https://example.gov.in/apply)\n"
            "## Documents Required\n- Enrollment proof\n- Enrollment proof\n"
            "Was this helpful?\nFooter content"
        )
        self.assertEqual(tables[0]["rows"], [["Diploma", "50%"]])
        self.assertEqual(sections["steps"], ["Apply online"])
        self.assertEqual(sections["documents"], ["Enrollment proof"])
        self.assertEqual(application, "https://example.gov.in/apply")
