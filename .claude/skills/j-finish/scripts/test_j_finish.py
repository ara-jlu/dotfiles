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

if __name__ == "__main__":
    unittest.main()
