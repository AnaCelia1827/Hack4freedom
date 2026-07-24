import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("lares.py")
SPEC = importlib.util.spec_from_file_location("lares", MODULE_PATH)
lares = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = lares
SPEC.loader.exec_module(lares)


class LaresPolicyTests(unittest.TestCase):
    def test_financial_paths_raise_risk(self):
        policy = {
            "path_rules": [{"pattern": "**/finance.py", "minimum_risk": "S2"}],
            "operation_rules": [],
        }
        self.assertEqual(lares.minimum_risk(["apps/api/bluejet_api/finance.py"], [], policy), "S2")

    def test_real_claim_rejects_mock_evidence(self):
        self.assertFalse(lares.evidence_satisfies_mode("MOCK", ["CA-005"], {"CA-005"}))
        self.assertTrue(lares.evidence_satisfies_mode("REAL", ["CA-005"], {"CA-005"}))

    def test_sensitive_evidence_is_detected(self):
        self.assertTrue(lares.sensitive_matches("nsec1qqqqqqqqqqqqqqqqqqqqqqqqqqqqqq"))
        self.assertTrue(lares.sensitive_matches("lnbc1qqqqqqqqqqqqqqqqqqqqqqqqqq"))
        self.assertFalse(lares.sensitive_matches("payment hash truncado ab12cd34"))

    def test_golden_gate_is_not_ready_without_evidence(self):
        gate = {"steps": [{"id": "GP-01", "evidence_ids": []}]}
        self.assertEqual(lares.gate_status(gate, {})[0], "NAO_PRONTO")

    def test_gate_rejects_evidence_that_does_not_cover_claim(self):
        gate = {"steps": [{"id": "GP-01", "requirements": ["RF-001"], "evidence_ids": ["EV-1"]}]}
        evidence = {
            "EV-1": {
                "claims": ["RF-002"],
                "subject_commit": "0" * 40,
                "environment": {"mode": "REAL"},
            }
        }
        self.assertEqual(lares.gate_status(gate, evidence)[0], "NAO_PRONTO")

    def test_gate_requires_same_current_commit(self):
        gate = {"steps": [{"id": "GP-01", "requirements": ["RF-001"], "evidence_ids": ["EV-1"]}]}
        evidence = {
            "EV-1": {
                "claims": ["RF-001"],
                "subject_commit": "a" * 40,
                "environment": {"mode": "REAL"},
            }
        }
        self.assertTrue(lares.gate_status(gate, evidence, "a" * 40)[0].startswith("ACEITO_NO_COMMIT"))
        self.assertEqual(lares.gate_status(gate, evidence, "b" * 40)[0], "REVALIDACAO_NECESSARIA")

    def test_subject_validation_accepts_exact_commit(self):
        self.assertTrue(lares.subject_is_current_or_control_descendant("a" * 40, "a" * 40))

    def test_unknown_path_defaults_to_high_risk(self):
        policy = {"default_unknown_risk": "S3", "path_rules": [], "operation_rules": []}
        self.assertEqual(lares.minimum_risk(["mystery/path"], [], policy), "S3")

    def test_authorization_does_not_cover_sibling_path(self):
        self.assertTrue(lares.path_is_authorized("docs/controle/**", ["docs/controle/**"]))
        self.assertFalse(lares.path_is_authorized("apps/api/**", ["docs/controle/**"]))

    def test_empty_collection_is_allowed_as_required_field(self):
        report = lares.Report()
        lares.require_fields({"dependencies": []}, ["dependencies"], "sample", report)
        self.assertEqual(report.errors, [])


if __name__ == "__main__":
    unittest.main()
