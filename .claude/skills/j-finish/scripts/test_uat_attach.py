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

class FakeRunner:
    """`gh` の代わり。呼ばれたコマンド列を記録し、決めた応答を返す。"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, cmd):
        self.calls.append(cmd)
        out = self.responses.pop(0)
        if isinstance(out, Exception):
            raise out
        return out

class TestAttachEvidence(unittest.TestCase):
    RESULTS = (
        '{"n":1,"name":"開く","status":"PASS"}\n'
        '{"n":1,"name":"初期表示","file":"shot-01-shot.png","kind":"shot"}\n'
    )

    def test_stops_when_gh_is_too_old(self):
        runner = FakeRunner(["gh version 2.98.0 (2026-08-01)"])
        with self.assertRaises(ua.AttachError) as cm:
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: self.RESULTS)
        self.assertIn("2.99.0", str(cm.exception))
        self.assertEqual(len(runner.calls), 1)  # gh --version だけで止まる

    def test_does_nothing_when_there_is_no_evidence(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        out = ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                                 runner=runner,
                                 reader=lambda p: '{"n":1,"name":"x","status":"PASS"}\n')
        self.assertIsNone(out)
        self.assertEqual(len(runner.calls), 1)

    def test_returns_none_when_results_jsonl_is_missing(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])

        def missing(path):
            raise FileNotFoundError(path)

        self.assertIsNone(ua.attach_evidence("https://pr/1", ".uat-evidence/005",
                                             "005", runner=runner, reader=missing))

    def test_stops_over_the_50_file_cap(self):
        rows = "".join(
            '{"n":%d,"name":"s%d","file":"shot-%02d.png","kind":"shot"}\n' % (i, i, i)
            for i in range(1, 52))
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        with self.assertRaises(ua.AttachError) as cm:
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: rows)
        self.assertIn("51", str(cm.exception))

    def test_posts_the_comment_and_links_it_from_the_body(self):
        runner = FakeRunner([
            "gh version 2.100.0 (2026-09-03)",
            "## UAT 証跡\n\n| step |\n",                 # gh pr view --json body
            "https://github.com/o/r/pull/1#issuecomment-9",  # gh pr comment
            "",                                              # gh pr edit
        ])
        url = ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                                 runner=runner, reader=lambda p: self.RESULTS)
        self.assertEqual(url, "https://github.com/o/r/pull/1#issuecomment-9")
        comment = runner.calls[2]
        self.assertIn("--attach", comment)
        self.assertIn(".uat-evidence/005/shot-01-shot.png#初期表示", comment)
        self.assertEqual(runner.calls[3][:3], ["gh", "pr", "edit"])

    def test_does_not_swallow_a_failing_gh(self):
        runner = FakeRunner([
            "gh version 2.100.0 (2026-09-03)",
            "## UAT 証跡\n",
            ua.AttachError("gh exited 1: upload failed for shot-01-shot.png"),
        ])
        with self.assertRaises(ua.AttachError):
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: self.RESULTS)

    def test_raises_when_results_jsonl_read_fails_for_a_reason_other_than_missing(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])

        def denied(path):
            raise PermissionError(path)

        with self.assertRaises(ua.AttachError):
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=denied)

    def test_carries_the_comment_url_when_gh_pr_edit_fails(self):
        runner = FakeRunner([
            "gh version 2.100.0 (2026-09-03)",
            "## UAT 証跡\n\n| step |\n",                 # gh pr view --json body
            "https://github.com/o/r/pull/1#issuecomment-9",  # gh pr comment
            ua.AttachError("gh exited 1: validation failed"),  # gh pr edit
        ])
        with self.assertRaises(ua.AttachError) as cm:
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: self.RESULTS)
        self.assertIn("https://github.com/o/r/pull/1#issuecomment-9", str(cm.exception))

    def test_dry_run_touches_nothing_after_the_version_check(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        url = ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                                 dry_run=True, runner=runner,
                                 reader=lambda p: self.RESULTS)
        self.assertIsNone(url)
        self.assertEqual(len(runner.calls), 1)

if __name__ == "__main__":
    unittest.main()
