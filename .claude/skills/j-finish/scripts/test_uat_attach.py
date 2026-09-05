#!/usr/bin/env python3
"""uat_attach.py の純粋部分を固定する。stdlib の unittest のみ。

  python3 .claude/skills/j-finish/scripts/test_uat_attach.py
"""
import glob
import os
import shutil
import sys
import tempfile
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

    def test_replaces_an_existing_link_instead_of_stacking_a_second_one(self):
        # gh pr edit が落ちたあとの復旧手順は再実行なので、追記だと 2 本並ぶ。
        once = ua.body_with_evidence_link("## UAT 証跡\n\n| step |\n", "URL1")
        twice = ua.body_with_evidence_link(once, "URL2")
        self.assertEqual(twice.count("証跡コメント:"), 1)
        self.assertIn("証跡コメント: URL2", twice)
        self.assertNotIn("URL1", twice)


class TestValidateShots(unittest.TestCase):
    """アップロード前の最後の関門。添付は取り消せないので黙って通さない。"""

    def _validate(self, shots, links=()):
        return ua.validate_shots(
            ".uat-evidence/005", shots,
            realpath=lambda p: os.path.normpath(os.path.join("/repo", p)),
            islink=lambda p: p in links)

    def test_accepts_a_plain_basename(self):
        self.assertIsNone(self._validate([{"name": "x", "file": "shot-01.png"}]))

    def test_rejects_a_path_escaping_the_evidence_dir(self):
        with self.assertRaises(ua.AttachError):
            self._validate([{"name": "x", "file": "../../.ssh/id_rsa"}])

    def test_rejects_a_symlink(self):
        with self.assertRaises(ua.AttachError) as cm:
            self._validate([{"name": "x", "file": "shot-01.png"}],
                           links=(".uat-evidence/005/shot-01.png",))
        self.assertIn("symlink", str(cm.exception))

    def test_rejects_a_row_without_a_file(self):
        with self.assertRaises(ua.AttachError):
            self._validate([{"name": "x"}])
        with self.assertRaises(ua.AttachError):
            self._validate([{"name": "x", "file": "  "}])

    def test_rejects_anything_that_is_not_a_plain_basename(self):
        # NUL は subprocess が ValueError で落とす (OSError ではないので
        # _run を素通りする)。`#` は gh の <file>#<alt> 区切りなので、含むと
        # gh が見るパスが検査した文字列とずれる。`/` は絶対パスと `..` と
        # サブディレクトリをまとめて閉じる。
        for bad in ["a\x00.png", "a.png#alt", "/etc/passwd", "sub/a.png",
                    "..\\a.png", ".", ".."]:
            with self.subTest(file=bad), self.assertRaises(ua.AttachError):
                self._validate([{"name": "x", "file": bad}])


class TestValidateShotsOnDisk(unittest.TestCase):
    """本物の os.path を通した封じ込め。ここが最後の関門なので実物で見る。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.evidence = os.path.join(self.tmp, "evidence")
        os.mkdir(self.evidence)
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_accepts_a_real_file_inside_the_dir(self):
        open(os.path.join(self.evidence, "shot-01.png"), "w").close()
        self.assertIsNone(
            ua.validate_shots(self.evidence, [{"name": "x", "file": "shot-01.png"}]))

    def test_rejects_a_symlink_pointing_outside(self):
        secret = os.path.join(self.tmp, "secret.txt")
        open(secret, "w").close()
        os.symlink(secret, os.path.join(self.evidence, "shot-01.png"))
        with self.assertRaises(ua.AttachError):
            ua.validate_shots(self.evidence, [{"name": "x", "file": "shot-01.png"}])

    def test_rejects_a_traversal_through_a_symlinked_parent(self):
        # 親が symlink のケースは islink(最終要素) では捕まらないが、
        # そもそも `/` を含む時点で basename 規則が先に落とす。
        os.symlink(self.tmp, os.path.join(self.evidence, "up"))
        with self.assertRaises(ua.AttachError):
            ua.validate_shots(self.evidence,
                              [{"name": "x", "file": "up/secret.txt"}])

    def test_rejects_a_lone_surrogate_in_file_or_name(self):
        # json.loads は通すが utf-8 に encode できない。素通しすると
        # dry-run の print と temp への書き出しで別々に例外が出る。
        with self.assertRaises(ua.AttachError):
            ua.validate_shots(self.evidence, [{"name": "x", "file": "\ud800.png"}])
        with self.assertRaises(ua.AttachError):
            ua.validate_shots(self.evidence,
                              [{"name": "\ud800bad", "file": "shot-01.png"}])

    def test_rejects_a_hash_in_the_alt_text(self):
        with self.assertRaises(ua.AttachError):
            ua.validate_shots(self.evidence,
                              [{"name": "a#b", "file": "shot-01.png"}])


class TestWriteTemp(unittest.TestCase):
    """書けなかった temp を残さない・素の例外を外に出さない。"""

    def _md_files(self):
        return set(glob.glob(os.path.join(tempfile.gettempdir(), "*.md")))

    def test_writes_and_returns_a_path(self):
        path = ua._write_temp("hello")
        self.addCleanup(os.unlink, path)
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "hello")

    def test_an_unencodable_body_raises_attach_error_and_leaves_no_file(self):
        before = self._md_files()
        with self.assertRaises(ua.AttachError):
            ua._write_temp("\ud800bad")
        self.assertEqual(self._md_files() - before, set())

    def test_a_failure_at_flush_also_raises_attach_error_and_leaves_no_file(self):
        # TextIOWrapper の write はバッファに積むだけで、実際の write(2) は
        # close の flush で走る。ENOSPC はこちら側にしか出ない。
        before = self._md_files()
        real_open = tempfile.NamedTemporaryFile

        class BrokenClose:
            def __init__(self, fh):
                self._fh = fh
                self.name = fh.name

            def write(self, text):
                return self._fh.write(text)

            def close(self):
                self._fh.close()
                raise OSError(28, "No space left on device")

        def broken(*a, **kw):
            return BrokenClose(real_open(*a, **kw))

        tempfile.NamedTemporaryFile = broken
        self.addCleanup(setattr, tempfile, "NamedTemporaryFile", real_open)
        with self.assertRaises(ua.AttachError):
            ua._write_temp("hello")
        self.assertEqual(self._md_files() - before, set())


class TestRun(unittest.TestCase):
    """`gh の失敗を握り潰さない` という契約そのもののテスト。"""

    def test_non_zero_exit_raises_with_the_stderr(self):
        with self.assertRaises(ua.AttachError) as cm:
            ua._run(["sh", "-c", "echo boom >&2; exit 3"])
        self.assertIn("exit 3", str(cm.exception))
        self.assertIn("boom", str(cm.exception))

    def test_a_null_byte_is_an_attach_error_not_a_raw_value_error(self):
        # subprocess は NUL に ValueError を投げる。OSError ではないので
        # _run の except を素通りし、j_finish の except AttachError も抜ける。
        with self.assertRaises(ua.AttachError):
            ua._run(["echo", "a\x00b"])

    def test_a_missing_binary_is_an_attach_error_not_a_raw_oserror(self):
        # 素の OSError は j_finish の except AttachError を素通りして
        # traceback で落ち、push/PR 済みの復旧案内が出ない。
        with self.assertRaises(ua.AttachError) as cm:
            ua._run(["definitely-not-a-real-binary-xyz", "--version"])
        self.assertIn("definitely-not-a-real-binary-xyz", str(cm.exception))


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

    def test_stops_when_gh_pr_comment_returns_no_url(self):
        # exit 0 なのに URL が空。ここで進むと本文に死んだラベルを書き、
        # 呼び出し側には falsy が返って「証跡なし」と区別できなくなる。
        runner = FakeRunner([
            "gh version 2.100.0 (2026-09-03)",
            "## UAT 証跡\n\n| step |\n",
            "",                                          # gh pr comment
        ])
        with self.assertRaises(ua.AttachError) as cm:
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: self.RESULTS)
        self.assertIn("URL", str(cm.exception))

    def test_stops_on_a_shot_pointing_outside_the_evidence_dir(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        rows = ('{"n":1,"name":"x","file":"../../../.ssh/id_rsa",'
                '"kind":"shot"}\n')
        with self.assertRaises(ua.AttachError):
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: rows)
        self.assertEqual(len(runner.calls), 1)  # gh を一度も叩かない

    def test_required_raises_when_results_jsonl_is_missing(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])

        def missing(path):
            raise FileNotFoundError(path)

        with self.assertRaises(ua.AttachError):
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=missing, required=True)

    def test_required_raises_when_there_are_no_shots(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        with self.assertRaises(ua.AttachError):
            ua.attach_evidence(
                "https://pr/1", ".uat-evidence/005", "005", runner=runner,
                reader=lambda p: '{"n":1,"name":"x","status":"PASS"}\n',
                required=True)


if __name__ == "__main__":
    unittest.main()
