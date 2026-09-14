import contextlib
import io
import pathlib
import tempfile
import unittest

import measure_wraps
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

    def test_puts_a_space_between_a_code_span_and_an_em_dash(self):
        src = "`--slug EN-SLUG`\n— house-style に従う。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "`--slug EN-SLUG` — house-style に従う。\n")

    def test_puts_no_space_between_japanese_punctuation(self):
        """日本語どうしの結合点には空白を入れない。約物も日本語と見なす。"""
        src = "規則はこうである。ここでは\n「両側が日本語なら空白なし」と読む。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "規則はこうである。ここでは「両側が日本語なら空白なし」と読む。\n")

    def test_puts_no_space_after_a_full_width_period(self):
        """左が全角の句点なら、右が何であっても空白を入れない。

        文末で結合を止めるようになったので、この結合点は unwrap_text からは
        もう出ない (句点で終わる行はそこで切れる)。規則そのものは join_parts
        に残っているので、ここで直接押さえておく。読点 (、) の側は文末では
        ないため、いまも unwrap_text 経由で出る。
        """
        self.assertEqual(
            unwrap.join_parts(["実体パスへ解決される。",
                               "`brew upgrade tmux` で更新する。"]),
            "実体パスへ解決される。`brew upgrade tmux` で更新する。")

    def test_puts_no_space_after_a_full_width_comma(self):
        """読点でも同じ。"""
        src = "先に片づけてから、\n`--apply` で当てる。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "先に片づけてから、`--apply` で当てる。\n")

    def test_a_half_width_colon_is_not_an_exception(self):
        """: は半角なので例外に当たらず、空白が入る。

        記号どうし (: と `) の結合点でもあるので、「片側が ASCII 英数か」で
        判定すると空白が落ちる形をここで押さえている。
        """
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

        結合点の左が空文字になる。素朴に空白を入れると行末が半角空白2つに
        なり、意図しないハードブレイクが生まれる。
        """
        src = "- \n  日本語の本文が桁数で\n  折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "- 日本語の本文が桁数で折り返されている。\n")


class TestFences(unittest.TestCase):
    """フェンスの開閉。マーカーの文字と長さを見ないと内と外が入れ替わる。

    markdown でフェンスを閉じられるのは、開いたときと同じ文字で同じ長さ
    以上のマーカーだけである。以前はマーカーに当たるどの行でも判定を反転
    させていたため、4 個のバッククォートで開いたフェンスの中の 3 個の行で
    反転し、以降のフェンスの内と外が入れ替わって、本来コードである
    ```ts ブロックが本文として結合された。verify の 3 条件はこれを検出
    できない (文字は欠けず、構造の数も段落の頭のインデントも変わらない)。
    """

    def test_a_shorter_marker_inside_a_longer_fence_does_not_close_it(self):
        """4 個で開いたフェンスの中の 3 個の行は中身であって、閉じない。"""
        src = ("````text\n"
               "  ```\n"
               "````\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        expected = src.replace("本文が折り\n返されている。",
                               "本文が折り返されている。")
        self.assertEqual(unwrap.unwrap_text(src), expected)

    def test_a_normal_fence_after_a_nested_fence_is_still_code(self):
        """実際に壊れたケース。ts ブロックのコードが本文として結合された。

        入れ子のマーカー行が奇数個あると、そこから先のフェンスの内と外が
        入れ替わる。続く ```ts の開きマーカーが「閉じ」として食われ、
        中身のコードが本文の段落として結合される。
        """
        src = ("````text\n"
               "  ```\n"
               "````\n"
               "\n"
               "```ts\n"
               "// 日本語のコメント\n"
               "const a = 1\n"
               "```\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_backtick_marker_does_not_close_a_tilde_fence(self):
        src = ("~~~\n"
               "  ```\n"
               "~~~\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        expected = src.replace("本文が折り\n返されている。",
                               "本文が折り返されている。")
        self.assertEqual(unwrap.unwrap_text(src), expected)

    def test_a_longer_marker_closes_a_shorter_fence(self):
        """3 個で開いて 4 個で閉じるのは有効 (同じ長さ以上なら閉じる)。"""
        src = ("```\n"
               "中身である\n"
               "````\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        expected = src.replace("本文が折り\n返されている。",
                               "本文が折り返されている。")
        self.assertEqual(unwrap.unwrap_text(src), expected)

    def test_a_marker_with_an_info_string_does_not_close_a_fence(self):
        """閉じマーカーの行には情報文字列 (言語名) を書けない。"""
        src = ("```\n"
               "```ts\n"
               "中身である\n"
               "```\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        expected = src.replace("本文が折り\n返されている。",
                               "本文が折り返されている。")
        self.assertEqual(unwrap.unwrap_text(src), expected)

    def test_an_unclosed_fence_runs_to_the_end_of_the_file(self):
        src = ("```\n"
               "中身が折り\n"
               "返されている。\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_backtick_in_the_info_string_does_not_open_a_fence(self):
        """バッククォートのフェンスの情報文字列にバッククォートは書けない。

        `` ```a` の書き方 `` のような行は段落であってフェンスではない。
        これをフェンスとして開くと、以降のフェンスの内と外が入れ替わり、
        続く本物のフェンスの中のコードが本文として結合される。verify の 3
        条件はこれを検出できない。
        """
        src = ("```a` の書き方\n"
               "\n"
               "```\n"
               "// 日本語のコメントが折り\n"
               "返されている\n"
               "const a = 1\n"
               "```\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_tilde_fence_allows_a_backtick_in_the_info_string(self):
        """チルダのフェンスには情報文字列の制限が無い。"""
        src = ("~~~`a`\n"
               "中身が折り\n"
               "返されている\n"
               "~~~\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_deeply_indented_marker_does_not_close_a_fence(self):
        """閉じマーカーのインデントは開きから 3 桁まで。4 桁以上は中身。"""
        src = ("```\n"
               "    ```\n"
               "中身が折り\n"
               "返されている\n"
               "```\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_marker_within_three_columns_still_closes_a_fence(self):
        src = ("```\n"
               "中身である\n"
               "   ```\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        expected = src.replace("本文が折り\n返されている。",
                               "本文が折り返されている。")
        self.assertEqual(unwrap.unwrap_text(src), expected)

    def test_an_indented_fence_in_a_list_closes_at_the_same_depth(self):
        """リスト項目の中の 8 桁インデントのフェンスは同じ深さで閉じる。

        インデントを絶対の桁数で見ると、この形のフェンスが閉じられなくなり、
        以降のファイル全体が中身として扱われる。見るのは開きからの相対で
        ある。
        """
        src = ("- 項目\n"
               "\n"
               "    - 入れ子\n"
               "\n"
               "        ```\n"
               "        code\n"
               "        ```\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        expected = src.replace("本文が折り\n返されている。",
                               "本文が折り返されている。")
        self.assertEqual(unwrap.unwrap_text(src), expected)

    def test_the_fence_handling_matches_unwrap(self):
        """unwrap.py と measure_wraps.py のフェンスの扱いが一致する。"""
        markers = ["```", "````", "~~~", "~~~~", "```ts", "````md", "~~~ js",
                   "  ```", "``", "本文", "```  ", "~~~~~",
                   "```a` の書き方", "~~~`a`", "   ```", "    ```",
                   "        ```", "        ```ts"]
        for line in markers:
            self.assertEqual(unwrap.fence_open(line),
                             measure_wraps.fence_open(line), line)
            for char in ("`", "~"):
                for length in (3, 4):
                    for indent in (0, 3, 8):
                        self.assertEqual(
                            unwrap.fence_closes(line, char, length, indent),
                            measure_wraps.fence_closes(line, char, length,
                                                       indent),
                            (line, char, length, indent))

    def test_measure_does_not_count_wraps_inside_a_nested_fence(self):
        """4 個で開いたフェンスの中の 3 個の行で内と外が入れ替わらない。

        入れ替わると、フェンスの中のコード行を段落行として数え、本来の
        段落行をフェンスの中として数えないので、残量の数が両側に狂う。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "a.md"
            path.write_text("````text\n"
                            "  ```\n"
                            "````\n"
                            "\n"
                            "本文が折り\n"
                            "返されている。\n"
                            "\n"
                            "```ts\n"
                            "const a = 1\n"
                            "```\n", encoding="utf-8")
            self.assertEqual(measure_wraps.classify(path), (2, 1, 1))

    def test_measure_does_not_open_a_fence_on_a_backtick_info_string(self):
        """情報文字列にバッククォートを含む行はフェンスを開かない。

        開いてしまうと、以降のフェンスの内と外が入れ替わり、コード行を
        段落行として数えて残量の数が両側に狂う。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "a.md"
            path.write_text("```a` の書き方\n"
                            "\n"
                            "```ts\n"
                            "const a = 1\n"
                            "```\n"
                            "\n"
                            "本文が折り\n"
                            "返されている。\n", encoding="utf-8")
            self.assertEqual(measure_wraps.classify(path), (3, 1, 1))

    def test_measure_does_not_close_a_fence_on_a_deeply_indented_marker(self):
        """開きから 4 桁以上深いマーカーは中身であって、閉じない。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "a.md"
            path.write_text("```\n"
                            "    ```\n"
                            "code is\n"
                            "wrapped\n"
                            "```\n"
                            "\n"
                            "本文が折り\n"
                            "返されている。\n", encoding="utf-8")
            self.assertEqual(measure_wraps.classify(path), (2, 1, 1))

    def test_measure_treats_an_unclosed_fence_as_content_to_the_end(self):
        """閉じられないままファイルが終われば、最後まで中身として扱う。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "a.md"
            path.write_text("本文が折り\n"
                            "返されている。\n"
                            "\n"
                            "```\n"
                            "中身が折り\n"
                            "返されている\n", encoding="utf-8")
            self.assertEqual(measure_wraps.classify(path), (2, 1, 1))


class TestSentenceBoundaries(unittest.TestCase):
    """文末での改行は折り返しではないので結合しない。

    このタスクが問題にしているのは語や句の途中で割れることであり、文末は
    意味のある位置だから害が無い。当初「1段落＝1行」として文末の改行まで
    結合したが、それは規約を広く取りすぎていた。
    """

    def test_does_not_join_after_a_sentence_end(self):
        src = ("このスキルは全ステップを自動実行します。\n"
               "各ステップ完了後、必ず次のステップに進んでください。\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_does_not_join_after_a_sentence_end_with_a_closing_marker(self):
        """`。**` や `）。` のように閉じ記号が付いていても文末である。"""
        for tail in ("**", "*", "`", "」", "』", "】", "〕", ")", '"', "'"):
            src = f"一文目である。{tail}\n二文目が続く。\n"
            self.assertEqual(unwrap.unwrap_text(src), src, tail)
        src = "一文目である（注記）。\n二文目が続く。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_does_not_join_after_an_exclamation_or_a_question(self):
        for mark in "！？":
            src = f"本当にそうか{mark}\n次の文が続く。\n"
            self.assertEqual(unwrap.unwrap_text(src), src, mark)

    def test_joins_after_a_colon(self):
        """`：` `:` は文末ではない。次に続く内容の導入なので結合する。"""
        src = "**Task 作成（tasks db）：**\n本文が続く。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "**Task 作成（tasks db）：** 本文が続く。\n")
        src = "superpowers を使う:\n`brainstorming` から始める。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "superpowers を使う: `brainstorming` から始める。\n")

    def test_still_joins_a_phrase_broken_mid_way(self):
        """句の途中で割れている行はこれまでどおり結合する。"""
        src = "日本語の本文が桁数で\n折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "日本語の本文が桁数で折り返されている。\n")

    def test_joins_each_side_of_a_sentence_boundary_separately(self):
        """文末で止めたあとも、その先の折り返しは結合する。"""
        src = ("一文目が桁数で\n"
               "折り返されている。\n"
               "二文目も桁数で\n"
               "折り返されている。\n")
        self.assertEqual(unwrap.unwrap_text(src),
                         "一文目が桁数で折り返されている。\n"
                         "二文目も桁数で折り返されている。\n")

    def test_keeps_the_indent_of_a_continuation_line_after_a_sentence_end(self):
        """文末で止めた次の行も、リストの中ならインデントを保つ。

        落とすと段落が桁 0 に出てリストがそこで切れる。
        """
        src = ("- 箇条書きの項目である。\n"
               "  二文目が桁数で\n"
               "  折り返されている。\n")
        self.assertEqual(unwrap.unwrap_text(src),
                         "- 箇条書きの項目である。\n"
                         "  二文目が桁数で折り返されている。\n")

    def test_a_sentence_split_paragraph_stays_one_paragraph(self):
        """結合を止めるだけで、段落は分割しない (空行を入れない)。"""
        src = "一文目である。\n二文目である。\n\n次の段落。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_the_result_is_idempotent(self):
        src = ("一文目が桁数で\n折り返されている。\n二文目も桁数で\n"
               "折り返されている。\n")
        once = unwrap.unwrap_text(src)
        self.assertEqual(unwrap.unwrap_text(once), once)


class TestJoinParts(unittest.TestCase):
    """join_parts を直接呼ぶ。unwrap_text 経由では通らない結合点を押さえる。"""

    def test_an_empty_side_adds_no_space(self):
        """どちらかが空なら結合点そのものが無いので、空白を入れない。

        unwrap.py の明示のガードが受け持つ形である。ガードが無くても
        `"" in JA_PUNCT` が真になるので結果は同じ (つまりガードを外しても
        テストは通る)。ここで固定しているのは分岐の有無ではなく、**空側に
        空白を入れない**という結合点の振る舞いそのものである。
        """
        self.assertEqual(unwrap.join_parts(["", "日本語の本文"]), "日本語の本文")
        self.assertEqual(unwrap.join_parts(["", "ASCII text"]), "ASCII text")
        self.assertEqual(unwrap.join_parts(["本文である。", ""]), "本文である。")
        self.assertEqual(unwrap.join_parts(["ASCII text", ""]), "ASCII text")

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


def _run_measure(argv):
    """measure_wraps.main を走らせ、(終了コード, 標準出力) を返す。"""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = measure_wraps.main(argv)
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

    def test_a_worktree_inside_the_target_is_skipped(self):
        """対象の内側に worktrees/ があれば、その中は除外する。

        接頭辞 `"/.claude/worktrees/"` で判定していたときは、対象を
        `<repo>/.claude` にすると相対パスが `/worktrees/...` になって一致
        せず、**進行中の別ブランチの worktree を書き換えていた**。
        notes/plan の Step 2 が案内しているのがまさにこの形である。
        """
        claude = self.tmp / ".claude"
        self._write(".claude/worktrees/feature-009/notes/a.md")
        self._write(".claude/skills/j-log/SKILL.md")
        code, output = _run_main([str(claude)])
        self.assertEqual(code, 0)
        self.assertIn("変換する (dry-run): 1 / 変更なし: 0 / 失敗: 0", output)
        self.assertNotIn("worktrees", output)

    def test_a_nonexistent_target_is_an_error(self):
        """打ち間違いは黙って 0 件にせず、その旨を出して 2 で終わる。"""
        code, output = _run_main([str(self.tmp / "notes-typo")])
        self.assertEqual(code, 2)
        self.assertIn("対象がディレクトリとして存在しない", output)
        self.assertNotIn("変換する", output)

    def test_a_file_passed_as_a_target_is_an_error(self):
        """ディレクトリでなければ、存在していてもエラーにする。"""
        path = self._write("notes/a.md")
        code, output = _run_main([str(path)])
        self.assertEqual(code, 2)
        self.assertIn("対象がディレクトリとして存在しない", output)

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


class TestMeasureWraps(unittest.TestCase):
    """measure_wraps.py は unwrap.py と同じ除外・同じ引数の扱いであること。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_the_skip_list_matches_unwrap(self):
        """除外の定義が2つのファイルで同じであること。

        片方だけが数えると、変換しないと決めた場所の折り返しが残量に出て、
        直し切れない数がいつまでも残る。
        """
        self.assertEqual(measure_wraps.SKIP_PARTS, unwrap.SKIP_PARTS)

    def test_the_sentence_end_pattern_matches_unwrap(self):
        """文末の定義も2つのファイルで同じであること。

        片方だけが文末を折り返しと見なすと、結合しないと決めた改行が残量に
        出て、直し切れない数がいつまでも残る。
        """
        self.assertEqual(measure_wraps.SENTENCE_END.pattern,
                         unwrap.SENTENCE_END.pattern)

    def test_a_sentence_end_is_not_counted_as_a_wrap(self):
        """文末で終わる行は、次が段落の続きでも折り返しに数えない。"""
        path = self.tmp / "a.md"
        path.write_text("一文目である。\n二文目である。\n", encoding="utf-8")
        body, cont, cont_ja = measure_wraps.classify(path)
        self.assertEqual((body, cont, cont_ja), (2, 0, 0))

    def test_a_mid_phrase_wrap_is_still_counted(self):
        path = self.tmp / "b.md"
        path.write_text("日本語の本文が桁数で\n折り返されている。\n",
                        encoding="utf-8")
        body, cont, cont_ja = measure_wraps.classify(path)
        self.assertEqual((body, cont, cont_ja), (2, 1, 1))

    def test_it_skips_the_same_directories(self):
        """除外の判定そのものも一致する (対象の内側でも外側でも)。"""
        base = self.tmp / ".claude"
        inside = base / "worktrees" / "feature-009" / "notes" / "a.md"
        outside = base / "skills" / "j-log" / "SKILL.md"
        for path in (inside, outside):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("日本語の本文が桁数で\n折り返されている。\n",
                            encoding="utf-8")
        self.assertTrue(unwrap.is_skipped(inside, base))
        self.assertTrue(measure_wraps.is_skipped(inside, base))
        self.assertFalse(unwrap.is_skipped(outside, base))
        self.assertFalse(measure_wraps.is_skipped(outside, base))

    def test_no_target_directory_is_an_error(self):
        code, output = _run_measure([])
        self.assertEqual(code, 2)
        self.assertIn("使い方", output)

    def test_a_nonexistent_target_is_an_error(self):
        code, output = _run_measure([str(self.tmp / "notes-typo")])
        self.assertEqual(code, 2)
        self.assertIn("対象がディレクトリとして存在しない", output)


if __name__ == "__main__":
    unittest.main()
