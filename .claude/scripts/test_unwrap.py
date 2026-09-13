import contextlib
import io
import pathlib
import tempfile
import unittest

import unwrap

class TestUnwrapText(unittest.TestCase):
    def test_joins_a_wrapped_japanese_paragraph(self):
        src = "日本語の本文が桁数で\n折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "日本語の本文が桁数で折り返されている。\n")

    def test_leaves_an_english_paragraph_alone(self):
        src = "This paragraph is wrapped\nat a column limit.\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_puts_a_space_where_either_side_is_ascii(self):
        src = "設計は Claude\nCode の上で動く。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "設計は Claude Code の上で動く。\n")

    def test_puts_a_space_at_a_japanese_to_ascii_boundary(self):
        src = "この規約は\nCLAUDE.md に置く。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "この規約は CLAUDE.md に置く。\n")

    def test_judges_japanese_by_paragraph_not_by_line(self):
        """英語の行で始まっても、段落に日本語があれば段落ごと結合する。"""
        src = "The design is simple\nだが適用範囲は広い。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "The design is simple だが適用範囲は広い。\n")

    def test_keeps_a_two_space_hard_break(self):
        src = "一行目で明示的に改行する。  \n二行目である。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_keeps_a_backslash_hard_break(self):
        src = "一行目で明示的に改行する。\\\n二行目である。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_a_fenced_block_alone(self):
        src = "```\nコードの中は\n折り返しても触らない。\n```\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_frontmatter_alone(self):
        src = "---\ntitle: あ\ntag: [document]\n---\n\n本文が折り\n返されている。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "---\ntitle: あ\ntag: [document]\n---\n\n本文が折り返されている。\n")

    def test_leaves_a_table_alone(self):
        src = "| 列 | 値 |\n|---|---|\n| あ | い |\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_a_heading_and_a_blockquote_alone(self):
        src = "## 見出し\n\n> 引用の本文が\n> 続く。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_joins_a_wrapped_list_item(self):
        src = "- 箇条書きの本文が\n  折り返されている。\n- 次の項目。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "- 箇条書きの本文が折り返されている。\n- 次の項目。\n")

    def test_keeps_a_nested_list_item_separate(self):
        src = "- 親の項目\n  - 子の項目\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_keeps_blank_lines_between_paragraphs(self):
        src = "最初の段落が折り\n返されている。\n\n次の段落も折り\n返されている。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "最初の段落が折り返されている。\n\n次の段落も折り返されている。\n")

    def test_leaves_an_indented_code_block_alone(self):
        src = "本文である。\n\n    コードの中は\n    折り返しても触らない。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_a_paragraph_containing_a_hard_break_alone(self):
        """ハードブレイクを含む段落は、その先が折り返されていても触らない。"""
        src = "一行目で明示的に改行する。  \n二行目が桁数で\n折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_keeps_the_indent_of_a_continuation_paragraph_in_a_bullet_item(self):
        """箇条書きの項目の中の継続段落は、結合してもインデントを保つ。

        インデントが落ちると段落が桁 0 に出て、リストがそこで切れる。
        verify はリスト項目の数も段落テキストも変わらないため検出できない。
        """
        src = ("- 箇条書きの項目である。\n"
               "\n"
               "  項目の中の段落が桁数で\n"
               "  折り返されている。\n"
               "\n"
               "- 次の項目。\n")
        self.assertEqual(
            unwrap.unwrap_text(src),
            "- 箇条書きの項目である。\n"
            "\n"
            "  項目の中の段落が桁数で折り返されている。\n"
            "\n"
            "- 次の項目。\n")

    def test_keeps_the_indent_of_a_continuation_paragraph_in_a_numbered_item(self):
        """番号付きリストの継続段落 (3スペース) でも同じ。"""
        src = ("1. 番号付きの項目である。\n"
               "\n"
               "   継続の段落が桁数で\n"
               "   折り返されている。\n"
               "\n"
               "2. 次の項目。\n")
        self.assertEqual(
            unwrap.unwrap_text(src),
            "1. 番号付きの項目である。\n"
            "\n"
            "   継続の段落が桁数で折り返されている。\n"
            "\n"
            "2. 次の項目。\n")

    def test_keeps_the_indent_of_a_paragraph_it_does_not_touch(self):
        """畳まない段落 (ハードブレイクを含む) でもインデントは元のまま。"""
        src = "- 項目である。\n\n  明示的に改行する。  \n  二行目である。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_puts_a_space_between_two_symbols(self):
        """記号どうしの結合点にも空白が入る (どちらも日本語ではないため)。"""
        src = "superpowers を使う:\n`brainstorming` から始める。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "superpowers を使う: `brainstorming` から始める。\n")

    def test_puts_a_space_between_a_code_span_and_an_em_dash(self):
        src = "`--slug EN-SLUG`\n— house-style に従う。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "`--slug EN-SLUG` — house-style に従う。\n")

    def test_puts_no_space_between_japanese_punctuation(self):
        """日本語どうしの結合点には空白を入れない。約物も日本語と見なす。"""
        src = "規則はこうである。\n「両側が日本語なら空白なし」と読む。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "規則はこうである。「両側が日本語なら空白なし」と読む。\n")

    def test_puts_no_space_after_a_full_width_period(self):
        """左が全角の句点なら、右が何であっても空白を入れない。"""
        src = "実体パスへ解決される。\n`brew upgrade tmux` で更新する。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "実体パスへ解決される。`brew upgrade tmux` で更新する。\n")

    def test_puts_no_space_after_a_full_width_comma(self):
        """読点でも同じ。"""
        src = "先に片づけてから、\n`--apply` で当てる。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "先に片づけてから、`--apply` で当てる。\n")

    def test_a_half_width_colon_is_not_an_exception(self):
        """: は半角なので例外に当たらず、空白が入る。"""
        src = "superpowers を使う:\n`brainstorming` から始める。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "superpowers を使う: `brainstorming` から始める。\n")

    def test_puts_no_space_before_a_full_width_opening_paren(self):
        """右が全角の開き括弧なら、左が何であっても空白を入れない。

        句読点の例外の鏡の側である。片側だけにすると、左が非日本語のときに
        `` `.claude` `` + `（対象は…` のような箇所へ空白が入る。
        """
        src = "対象は `.claude`\n（対象ディレクトリからの相対で判定する）。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "対象は `.claude`（対象ディレクトリからの相対で判定する）。\n")

    def test_puts_no_space_before_a_full_width_opening_quote(self):
        """「 でも同じ。"""
        src = "**画像は入れない**\n「画像は入れない」と読む。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "**画像は入れない**「画像は入れない」と読む。\n")

    def test_puts_no_space_before_the_other_full_width_brackets(self):
        """『【〔 も開き括弧として扱う。"""
        for bracket in "『【〔":
            src = f"`unwrap.py`\n{bracket}日本語の本文である。\n"
            self.assertEqual(unwrap.unwrap_text(src),
                             f"`unwrap.py`{bracket}日本語の本文である。\n")

    def test_an_ascii_opening_paren_is_not_an_exception(self):
        """( は半角なので例外に当たらず、空白が入る。"""
        src = "対象は `.claude`\n(半角の括弧である) と読む。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "対象は `.claude` (半角の括弧である) と読む。\n")

    def test_a_marker_only_line_does_not_gain_a_double_space(self):
        """本文がマーカーの次の行から始まっても空白は増えない。

        結合点の左が空文字になる。空文字は in 判定でどの文字列にも含まれる
        ので、明示的に落としておかないと `left in JA_PUNCT` が偽の真になる。
        逆に素朴に空白を入れると行末が半角空白2つになり、意図しないハード
        ブレイクが生まれる。
        """
        src = "- \n  日本語の本文が桁数で\n  折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "- 日本語の本文が桁数で折り返されている。\n")

class TestVerify(unittest.TestCase):
    def test_a_clean_unwrap_has_no_problems(self):
        before = "日本語の本文が桁数で\n折り返されている。\n"
        after = unwrap.unwrap_text(before)
        self.assertEqual(unwrap.verify(before, after), [])

    def test_dropped_characters_are_caught(self):
        before = "日本語の本文が桁数で\n折り返されている。\n"
        self.assertTrue(unwrap.verify(before, "日本語の本文が桁数で\n"))

    def test_reordered_characters_are_caught(self):
        before = "あいうえお\nかきくけこ\n"
        self.assertTrue(unwrap.verify(before, "かきくけこあいうえお\n"))

    def test_a_lost_heading_is_caught(self):
        before = "## 見出し\n\n本文である。\n"
        self.assertTrue(unwrap.verify(before, "見出し\n\n本文である。\n"))

    def test_a_lost_list_item_is_caught(self):
        before = "- 一つ目\n- 二つ目\n"
        self.assertTrue(unwrap.verify(before, "- 一つ目二つ目\n"))

    def test_a_lost_table_row_is_caught(self):
        before = "| 列 |\n|---|\n| あ |\n"
        self.assertTrue(unwrap.verify(before, "| 列 |\n|---|\n"))

    def test_added_join_spaces_are_not_a_problem(self):
        """結合で入る空白は差ではない (比較は空白を除いて行う)。"""
        before = "この規約は\nCLAUDE.md に置く。\n"
        after = "この規約は CLAUDE.md に置く。\n"
        self.assertEqual(unwrap.verify(before, after), [])

    def test_a_dropped_paragraph_indent_is_caught(self):
        """インデントを落としてリストを切る壊し方を捕まえる。

        リスト項目の数は変わらず、段落テキストの比較は空白を無視するので、
        既存の2条件はどちらもこれを素通りする。
        """
        before = ("- 箇条書きの項目である。\n"
                  "\n"
                  "  項目の中の段落が桁数で\n"
                  "  折り返されている。\n"
                  "\n"
                  "- 次の項目。\n")
        after = ("- 箇条書きの項目である。\n"
                 "\n"
                 "項目の中の段落が桁数で折り返されている。\n"
                 "\n"
                 "- 次の項目。\n")
        self.assertEqual(unwrap._squeeze(before), unwrap._squeeze(after))
        self.assertTrue(unwrap.verify(before, after))

    def test_a_table_without_leading_pipes_is_caught(self):
        """先頭に | が無い表は結合されて壊れる。verify がそれを止める。"""
        before = "列1 | 列2\n---|---\nあ | い\n"
        after = unwrap.unwrap_text(before)
        self.assertTrue(unwrap.verify(before, after))

def _run_main(argv):
    """main を走らせ、(終了コード, 標準出力) を返す。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = unwrap.main(argv)
    return code, buffer.getvalue()


class TestMain(unittest.TestCase):
    """main の除外パス判定と引数の扱い。

    ここが壊れると「変更なし・失敗 0」と出て成功に見える。unwrap_text と
    verify のテストはこの壊れ方を一切守らない。
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _write(self, relative):
        path = self.tmp / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("日本語の本文が桁数で\n折り返されている。\n",
                        encoding="utf-8")
        return path

    def test_a_target_inside_a_worktree_is_not_skipped(self):
        """対象ディレクトリ自身が .claude/worktrees/ の下にあっても除外しない。

        除外は対象ディレクトリからの相対で判定する。絶対パスで判定すると
        worktree の中で走らせた瞬間に全件が除外され、「変更なし・失敗 0」と
        出て成功に見える。
        """
        target = self.tmp / ".claude" / "worktrees" / "feature-008" / "notes"
        self._write(".claude/worktrees/feature-008/notes/a.md")
        code, output = _run_main([str(target)])
        self.assertEqual(code, 0)
        self.assertIn("変換する (dry-run): 1 / 変更なし: 0 / 失敗: 0", output)

    def test_a_skipped_directory_inside_the_target_is_still_skipped(self):
        """対象より内側の除外パスは、これまでどおり除外する。"""
        self._write("node_modules/pkg/a.md")
        self._write(".superpowers/sdd/task-1.md")
        code, output = _run_main([str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertIn("変換する (dry-run): 0 / 変更なし: 0 / 失敗: 0", output)

    def test_dry_run_does_not_write(self):
        path = self._write("notes/a.md")
        before = path.read_text(encoding="utf-8")
        _run_main([str(self.tmp)])
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_apply_writes(self):
        path = self._write("notes/a.md")
        code, _ = _run_main([str(self.tmp), "--apply"])
        self.assertEqual(code, 0)
        self.assertEqual(path.read_text(encoding="utf-8"),
                         "日本語の本文が桁数で折り返されている。\n")

    def test_no_target_directory_is_an_error(self):
        """対象ディレクトリを渡し忘れたら、使い方を出して 2 で終わる。"""
        code, output = _run_main([])
        self.assertEqual(code, 2)
        self.assertIn("使い方", output)
        code, output = _run_main(["--apply"])
        self.assertEqual(code, 2)
        self.assertIn("使い方", output)

    def test_an_unreadable_file_is_reported_and_the_run_continues(self):
        """読めないファイルが1件あっても、残りの処理は続く。"""
        (self.tmp / "notes").mkdir(parents=True, exist_ok=True)
        (self.tmp / "notes" / "broken.md").write_bytes(b"\xff\xfe\x00broken")
        self._write("notes/ok.md")
        code, output = _run_main([str(self.tmp)])
        self.assertEqual(code, 1)
        self.assertIn("FAILED", output)
        self.assertIn("変換する (dry-run): 1 / 変更なし: 0 / 失敗: 1", output)


if __name__ == "__main__":
    unittest.main()
