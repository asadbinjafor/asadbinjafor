"""Regression checks for automated data refreshes, not the decorative artwork."""
import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/f"{name}.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refresh=load("refresh_stats")
build=load("build_profile")


class RefreshTests(unittest.TestCase):
    def test_contribution_counts_and_chronological_order(self):
        html='''<td data-date="2026-01-02" id="b" data-level="4"></td>
        <tool-tip for="b">1,234 contributions on January 2nd.</tool-tip>
        <td data-date="2026-01-01" id="a" data-level="0"></td>
        <tool-tip for="a">No contributions on January 1st.</tool-tip>
        <td data-date="2026-01-03" id="c" data-level="1"></td>
        <tool-tip for="c">1 contribution on January 3rd.</tool-tip>'''
        days=refresh.parse_contributions(html)
        self.assertEqual([d["count"] for d in days],[0,1234,1])
        self.assertEqual(days[0]["date"],"2026-01-01")

    def test_missing_counts_fail_instead_of_publishing_zero(self):
        with self.assertRaises(ValueError):
            refresh.parse_contributions('<td data-date="2026-01-01" id="a" data-level="2"></td>')

    def test_month_labels_roll_into_a_different_year(self):
        labels=build.month_labels(date(2026,12,20),date(2027,3,20))
        self.assertEqual([label for _,label in labels],["JAN","FEB","MAR"])
        labels=build.month_labels(date(2026,11,1),date(2027,2,15))
        self.assertEqual([label for _,label in labels],["NOV","DEC","JAN","FEB"])

    def test_missing_or_duplicate_days_are_rejected(self):
        template='<td data-date="{day}" id="{key}" data-level="0"></td><tool-tip for="{key}">No contributions on January.</tool-tip>'
        for second_day in ("2026-01-01","2026-01-03"):
            with self.subTest(second_day=second_day),self.assertRaises(ValueError):
                refresh.parse_contributions(
                    template.format(day="2026-01-01",key="a")+
                    template.format(day=second_day,key="b"))

    def test_readme_versions_refresh_without_duplicate_queries(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"assets").mkdir()
            for asset in ("stats.svg","stats-mobile.svg","activity.svg"):
                (root/"assets"/asset).write_text("<svg/>")
            original=('Keep this biography.\n<sub>Activity snapshot: **20 October 2026**</sub>\n'
                      '<img src="./assets/stats.svg?v=old"/><source srcset="./assets/stats-mobile.svg"/>'
                      '<img src="./assets/activity.svg" alt="My GitHub contribution history from October 19, 2025 to October 20, 2026, with a decorative animation"/>')
            data={"updated":"2027-01-02","updated_at":"2027-01-02T06:17:00+06:00",
                  "contributions":[{"date":"2026-01-01"},{"date":"2027-01-02"}]}
            with patch.object(refresh,"ROOT",root):
                result=refresh.update_readme(original,data)
                self.assertEqual(refresh.update_readme(result,data),result)
            self.assertIn("2 January 2027, 06:17 BST",result)
            self.assertIn("January 1, 2026 to January 2, 2027",result)
            self.assertEqual(result.count("?v="),3)
            self.assertTrue(result.startswith("Keep this biography."))


if __name__=="__main__":
    unittest.main()
