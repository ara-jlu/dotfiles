#!/usr/bin/env python3
"""uat_attach.py の純粋部分を固定する。stdlib の unittest のみ。

  python3 .claude/skills/j-finish/scripts/test_uat_attach.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uat_attach as ua

class TestParseGhVersion(unittest.TestCase):
    def test_parses_the_real_gh_output(self):
        text = "gh version 2.100.0 (2026-09-03)\nhttps://github.com/cli/cli/releases/tag/v2.100.0"
        self.assertEqual(ua.parse_gh_version(text), (2, 100, 0))

    def test_returns_none_when_unparseable(self):
        self.assertIsNone(ua.parse_gh_version("command not found"))

    def test_version_floor_is_2_99_0(self):
        self.assertEqual(ua.MIN_GH_VERSION, (2, 99, 0))
        self.assertLess(ua.parse_gh_version("gh version 2.98.1 (2026-08-01)"),
                        ua.MIN_GH_VERSION)
        self.assertGreaterEqual(ua.parse_gh_version("gh version 2.99.0 (2026-09-01)"),
                                ua.MIN_GH_VERSION)
        # 2.100.0 > 2.99.0 — 文字列比較なら逆転する組み合わせ
        self.assertGreaterEqual(ua.parse_gh_version("gh version 2.100.0 (2026-09-03)"),
                                ua.MIN_GH_VERSION)

class TestParseResults(unittest.TestCase):
    def test_keeps_valid_rows_and_counts_broken_ones(self):
        text = (
            '{"n":1,"name":"開く","status":"PASS"}\n'
            '{"n":1,"name":"初期表示","file":"shot-01-.png","kind":"shot"}\n'
            '{"n":2,"name":"壊れた行\n'
            '\n'
            '"just a string"\n'
        )
        rows, skipped = ua.parse_results(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(skipped, 2)

    def test_shot_rows_drops_judgement_rows(self):
        rows = [
            {"n": 1, "name": "開く", "status": "PASS"},
            {"n": 1, "name": "初期表示", "file": "a.png", "kind": "shot"},
        ]
        self.assertEqual(ua.shot_rows(rows), [rows[1]])

class TestIsVideo(unittest.TestCase):
    def test_classifies_by_extension(self):
        self.assertTrue(ua.is_video("clip-01-drag.webm"))
        self.assertTrue(ua.is_video("clip-01-drag.MP4"))
        self.assertFalse(ua.is_video("shot-01-open.png"))

class TestRenderComment(unittest.TestCase):
    def setUp(self):
        self.shots = [
            {"name": "初期表示", "file": "shot-01-shot.png"},
            {"name": "ドラッグ中", "file": "clip-01-drag.webm"},
        ]

    def test_images_are_referenced_inline_with_their_name_as_alt(self):
        body = ua.render_comment("005", self.shots)
        self.assertIn("![初期表示](./shot-01-shot.png)", body)

    def test_videos_are_not_referenced_so_gh_appends_a_player(self):
        body = ua.render_comment("005", self.shots)
        self.assertNotIn("(./clip-01-drag.webm)", body)
        self.assertIn("ドラッグ中", body)

    def test_escapes_brackets_in_the_alt_text(self):
        body = ua.render_comment("005", [{"name": "[重要] 表示", "file": "a.png"}])
        self.assertIn("![\\[重要\\] 表示](./a.png)", body)

class TestAttachArgs(unittest.TestCase):
    def test_pairs_each_path_with_its_name(self):
        args = ua.attach_args(".uat-evidence/005",
                              [{"name": "初期表示", "file": "shot-01-shot.png"}])
        self.assertEqual(
            args, ["--attach", ".uat-evidence/005/shot-01-shot.png#初期表示"])

    def test_falls_back_to_the_filename_when_name_is_empty(self):
        args = ua.attach_args(".uat-evidence/005", [{"name": "", "file": "a.png"}])
        self.assertEqual(args, ["--attach", ".uat-evidence/005/a.png"])

    def test_cap_is_50(self):
        self.assertEqual(ua.MAX_ATTACH, 50)

class TestBodyWithEvidenceLink(unittest.TestCase):
    def test_appends_inside_the_uat_section(self):
        body = "## UAT 証跡\n\n| step |\n\n## レビュー観点\n\n- x\n"
        out = ua.body_with_evidence_link(body, "https://example/pr#issuecomment-1")
        self.assertIn("証跡コメント: https://example/pr#issuecomment-1", out)
        self.assertLess(out.index("証跡コメント:"), out.index("## レビュー観点"))

    def test_appends_at_end_when_the_section_is_last(self):
        body = "## 概要\n\nx\n\n## UAT 証跡\n\n| step |\n"
        out = ua.body_with_evidence_link(body, "URL")
        self.assertTrue(out.rstrip().endswith("証跡コメント: URL"))

    def test_returns_none_when_there_is_no_uat_section(self):
        self.assertIsNone(ua.body_with_evidence_link("## 概要\n\nx\n", "URL"))

if __name__ == "__main__":
    unittest.main()
