import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "test_chatbot.py"
SPEC = importlib.util.spec_from_file_location("test_chatbot", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ProjectContractTests(unittest.TestCase):
    def test_full_evaluation_keeps_15_cases(self):
        self.assertEqual(len(MODULE.QUESTIONS), 15)

    def test_full_evaluation_has_three_refusal_cases(self):
        self.assertEqual(sum(bool(q["out_of_scope"]) for q in MODULE.QUESTIONS), 3)

    def test_smoke_subset_has_five_cases_and_one_refusal(self):
        selected = [MODULE.QUESTIONS[i] for i in MODULE.SMOKE_INDICES]
        self.assertEqual(len(selected), 5)
        self.assertEqual(sum(bool(q["out_of_scope"]) for q in selected), 1)

    def test_smoke_subset_indices_are_stable(self):
        self.assertEqual(MODULE.SMOKE_INDICES, (0, 2, 7, 8, 10))

    def test_widget_bundle_is_pinned_and_placeholder_removed(self):
        html = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("flowise-embed@3.1.6", html)
        self.assertNotIn("REMPLACER_PAR_ID_CHATFLOW", html)

    def test_package_json_is_valid_and_has_test_script(self):
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("test", package["scripts"])


if __name__ == "__main__":
    unittest.main()
