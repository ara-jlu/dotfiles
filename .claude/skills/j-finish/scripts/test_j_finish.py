#!/usr/bin/env python3
"""j_finish.py の UAT 証跡チェックを固定する。

  python3 .claude/skills/j-finish/scripts/test_j_finish.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import j_finish as jf

class TestWarnUatEvidence(unittest.TestCase):
    def test_warns_when_ui_changed_without_a_local_evidence_run(self):
        warnings = jf._warn_uat_evidence(
            ["apps/web/src/App.tsx"], ".uat-evidence/005", exists=lambda p: False)
        self.assertEqual(len(warnings), 1)
        self.assertIn("pnpm uat", warnings[0])

    def test_quiet_when_the_evidence_run_exists(self):
        self.assertEqual(
            jf._warn_uat_evidence(["apps/web/src/App.tsx"], ".uat-evidence/005",
                                  exists=lambda p: True),
            [])

    def test_warns_when_no_evidence_dir_was_given_for_a_ui_change(self):
        warnings = jf._warn_uat_evidence(["apps/web/src/App.tsx"], None,
                                         exists=lambda p: True)
        self.assertEqual(len(warnings), 1)
        self.assertIn("--uat-evidence-dir", warnings[0])

    def test_e2e_only_changes_do_not_count_as_ui(self):
        self.assertEqual(
            jf._warn_uat_evidence(["apps/web/e2e/005.uat.spec.ts"], None,
                                  exists=lambda p: False),
            [])

    def test_warns_when_evidence_was_committed(self):
        warnings = jf._warn_uat_evidence(
            [".uat-evidence/005/shot-01.png"], ".uat-evidence/005",
            exists=lambda p: True)
        self.assertEqual(len(warnings), 1)
        self.assertIn("commit", warnings[0])

    def test_reports_both_problems_at_once(self):
        warnings = jf._warn_uat_evidence(
            ["apps/web/src/App.tsx", ".uat-evidence/005/shot-01.png"],
            ".uat-evidence/005", exists=lambda p: False)
        self.assertEqual(len(warnings), 2)


class TestPrUrlMissing(unittest.TestCase):
    def test_placeholder_pr_url_is_rejected(self):
        self.assertTrue(jf._pr_url_missing(jf.PLACEHOLDER_PR_URL))

    def test_empty_pr_url_is_rejected(self):
        self.assertTrue(jf._pr_url_missing(""))

    def test_real_pr_url_is_accepted(self):
        self.assertFalse(
            jf._pr_url_missing("https://github.com/acme/repo/pull/42"))


class TestAttachFailureMessage(unittest.TestCase):
    def test_message_names_recovery_details(self):
        msg = jf._attach_failure_message(
            RuntimeError("gh pr comment failed"),
            "https://github.com/acme/repo/pull/42",
            ".uat-evidence/005",
            "/repo/.claude/skills/j-finish/scripts",
            dry_run=False)
        self.assertIn("https://github.com/acme/repo/pull/42", msg)
        self.assertIn(".uat-evidence/005", msg)
        self.assertIn(
            "/repo/.claude/skills/j-finish/scripts/uat_attach.py", msg)
        self.assertIn("--no-pr", msg)

    def test_dry_run_message_does_not_claim_push_or_pr_creation(self):
        msg = jf._attach_failure_message(
            RuntimeError("gh 2.40.0 検出: gh 2.99.0 以上が必要です"),
            jf.PLACEHOLDER_PR_URL,
            ".uat-evidence/005",
            "/repo/.claude/skills/j-finish/scripts",
            dry_run=True)
        self.assertNotIn("push 済み", msg)
        self.assertNotIn("作成済み", msg)
        self.assertIn(".uat-evidence/005", msg)
        # 実際には何も実行されていないことを明言する。
        self.assertIn("push されておらず", msg)
        self.assertIn("作成されていません", msg)


if __name__ == "__main__":
    unittest.main()
