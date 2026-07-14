from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from realtool_loc.release_audit import audit_tree  # noqa: E402


class ReleaseAuditTests(unittest.TestCase):
    def audit_text(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "fixture.txt"
            path.write_text(text, encoding="utf-8")
            return audit_tree(Path(directory))

    def test_clean_public_text_passes(self) -> None:
        self.assertEqual(self.audit_text("Offline benchmark documentation.\nhttps://example.org/docs\n"), [])

    def test_local_user_path_is_rejected(self) -> None:
        violations = self.audit_text("Run /" + "Users/example/private/script.py")
        self.assertTrue(any("local path" in item for item in violations))

    def test_private_ip_is_rejected(self) -> None:
        violations = self.audit_text("endpoint = http://" + "10." + "10.20.15:4000/v1")
        self.assertTrue(any("private network" in item for item in violations))

    def test_credential_assignment_is_rejected(self) -> None:
        violations = self.audit_text('api_' + 'key = "secret-value"')
        self.assertTrue(any("credential" in item for item in violations))

    def test_repository_owner_identity_is_rejected(self) -> None:
        violations = self.audit_text("github.com/" + "kay" + "cer12/project")
        self.assertTrue(any("repository owner" in item for item in violations))

    def test_personal_email_is_rejected_but_neutral_identity_is_allowed(self) -> None:
        violations = self.audit_text("Contact person" + "@example.com")
        self.assertTrue(any("email" in item for item in violations))
        self.assertEqual(self.audit_text("Anonymous Authors <anonymous@invalid.example>"), [])

    def test_oversized_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "large.bin"
            path.write_bytes(b"x" * 64)
            violations = audit_tree(Path(directory), max_size_bytes=32)
            self.assertTrue(any("oversized" in item for item in violations))


if __name__ == "__main__":
    unittest.main()
