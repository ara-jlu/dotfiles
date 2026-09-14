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

    def test_keeps_a_hard_break_in_a_crlf_file(self):
        """**CRLF でも保護が外れない。** 判定は rstrip の前の行に当てるので `\\r` を許して読む。

        `\\r` を見ないと `本文  \\r` に一致せず、保護が**黙って**外れる。結合された結果は `_squeeze` も markdown-it も `\\r` を吸収するので**検証の 5 条件すべてを通る**。実データに CRLF は 0 件だが、`<pre>` と同じ基準で塞ぐ。
        """
        src = "本文が桁数で  \r\n折り返されている。\r\n"
        self.assertEqual(unwrap.unwrap_text(src), src)
        self.assertEqual(unwrap.verify(src, unwrap.unwrap_text(src)), [])

    def test_keeps_a_backslash_hard_break_in_a_crlf_file(self):
        src = "本文が桁数で\\\r\n折り返されている。\r\n"
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

        文末で結合を止めるようになったので、この結合点は unwrap_text からはもう出ない (句点で終わる行はそこで切れる)。規則そのものは join_parts に残っているので、ここで直接押さえておく。読点 (、) の側は文末ではないため、いまも unwrap_text 経由で出る。
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

        記号どうし (: と `) の結合点でもあるので、「片側が ASCII 英数か」で判定すると空白が落ちる形をここで押さえている。
        """
        src = "superpowers を使う:\n`brainstorming` から始める。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "superpowers を使う: `brainstorming` から始める。\n")

    def test_puts_no_space_before_a_full_width_opening_paren(self):
        """右が全角の開き括弧なら、左が何であっても空白を入れない。

        句読点の例外の鏡の側である。片側だけにすると、左が非日本語のときに `` `.claude` `` + `（対象は…` のような箇所へ空白が入る。
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

        結合点の左が空文字になる。素朴に空白を入れると行末が半角空白2つになり、意図しないハードブレイクが生まれる。
        """
        src = "- \n  日本語の本文が桁数で\n  折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "- 日本語の本文が桁数で折り返されている。\n")


class TestFences(unittest.TestCase):
    """フェンスの開閉。マーカーの文字と長さを見ないと内と外が入れ替わる。

    markdown でフェンスを閉じられるのは、開いたときと同じ文字で同じ長さ以上のマーカーだけである。以前はマーカーに当たるどの行でも判定を反転させていたため、4 個のバッククォートで開いたフェンスの中の 3 個の行で反転し、以降のフェンスの内と外が入れ替わって、本来コードである ```ts ブロックが本文として結合された。verify の 3 条件はこれを検出できない (文字は欠けず、構造の数も段落の頭のインデントも変わらない)。
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

        入れ子のマーカー行が奇数個あると、そこから先のフェンスの内と外が入れ替わる。続く ```ts の開きマーカーが「閉じ」として食われ、中身のコードが本文の段落として結合される。
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
        これをフェンスとして開くと、以降のフェンスの内と外が入れ替わり、続く本物のフェンスの中のコードが本文として結合される。verify の 3 条件はこれを検出できない。
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

    def test_a_tab_indented_marker_does_not_close_a_fence(self):
        """タブは 4 の倍数の桁まで展開する。`\\t```` は開きから 4 桁なので閉じない。

        インデント幅を `len()` で数えるとタブが 1 桁になり、この行がフェンスを閉じる。そこから先の内と外が入れ替わり、本来コードである領域が本文として結合される。**フェンスの入れ子・HTML ブロックに続く 3 件目の、開閉の範囲の取り違えである。**
        """
        src = ("```\n"
               "\t```\n"
               "中身が折り\n"
               "返されている\n"
               "```\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_tab_indented_marker_does_not_corrupt_the_227_shape(self):
        """実データ (joifup の notes/document/227-*) の形をそのまま固定する。

        4 桁インデントで開いたフェンスの中の `    \\t```` は、展開すると 8 桁で開きから 4 桁なので閉じない。次の `    ```` (開きと同じ 4 桁) が閉じる。この 1 行を取り違えると、以降のファイル全体の内と外が入れ替わった。

        **ブロックの種別までが参照パーサと一致するわけではない。** 最上位の 4 桁インデントは CommonMark ではフェンスではなくインデントされたコードブロックであり、unwrap はフェンスとして読む。ここで固定しているのは「中身を 1 文字も触らない」ことである。実データの 227 はこの形が外側のフェンスの中にあるので、種別の食い違いは表に出ない。
        """
        src = ("    ```joifup\n"
               "    \t```\n"
               "    ```\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        expected = src.replace("本文が折り\n返されている。",
                               "本文が折り返されている。")
        self.assertEqual(unwrap.unwrap_text(src), expected)
        self.assertEqual(unwrap.verify(src, unwrap.unwrap_text(src)), [])

    def test_indent_width_expands_tabs_to_the_next_tab_stop(self):
        self.assertEqual(unwrap.indent_width(""), 0)
        self.assertEqual(unwrap.indent_width("   "), 3)
        self.assertEqual(unwrap.indent_width("\t"), 4)
        self.assertEqual(unwrap.indent_width("  \t"), 4)
        self.assertEqual(unwrap.indent_width("    \t"), 8)
        self.assertEqual(unwrap.indent_width("\t\t"), 8)
        self.assertEqual(unwrap.indent_width("\t "), 5)

    def test_an_indented_fence_in_a_list_closes_at_the_same_depth(self):
        """リスト項目の中の 8 桁インデントのフェンスは同じ深さで閉じる。

        インデントを絶対の桁数で見ると、この形のフェンスが閉じられなくなり、以降のファイル全体が中身として扱われる。見るのは開きからの相対である。
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
                   "        ```", "        ```ts",
                   "\t```", "  \t```", "    \t```", "\t\t```", "\t~~~"]
        for line in markers:
            self.assertEqual(unwrap.fence_open(line),
                             measure_wraps.fence_open(line), line)
            for char in ("`", "~"):
                for length in (3, 4):
                    for indent in (0, 3, 4, 8):
                        self.assertEqual(
                            unwrap.fence_closes(line, char, length, indent),
                            measure_wraps.fence_closes(line, char, length,
                                                       indent),
                            (line, char, length, indent))

    def test_the_tab_expansion_matches_unwrap(self):
        """インデントの桁の数え方も両者で一致していなければならない。"""
        for indent in ("", " ", "   ", "    ", "\t", "  \t", "    \t", "\t\t",
                       "\t "):
            self.assertEqual(unwrap.indent_width(indent),
                             measure_wraps.indent_width(indent), repr(indent))

    def test_measure_does_not_close_a_fence_on_a_tab_indented_marker(self):
        """タブを展開すると開きから 4 桁なので閉じない。

        `len()` で数えると閉じたことになり、以降の内と外が入れ替わって、コード行を段落行として数える。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "a.md"
            path.write_text("```\n"
                            "\t```\n"
                            "code is\n"
                            "wrapped\n"
                            "```\n"
                            "\n"
                            "本文が折り\n"
                            "返されている。\n", encoding="utf-8")
            self.assertEqual(measure_wraps.classify(path), (2, 1, 1))

    def test_measure_does_not_count_wraps_inside_a_nested_fence(self):
        """4 個で開いたフェンスの中の 3 個の行で内と外が入れ替わらない。

        入れ替わると、フェンスの中のコード行を段落行として数え、本来の段落行をフェンスの中として数えないので、残量の数が両側に狂う。
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

        開いてしまうと、以降のフェンスの内と外が入れ替わり、コード行を段落行として数えて残量の数が両側に狂う。
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

    このタスクが問題にしているのは語や句の途中で割れることであり、文末は意味のある位置だから害が無い。当初「1段落＝1行」として文末の改行まで結合したが、それは規約を広く取りすぎていた。
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

        unwrap.py の明示のガードが受け持つ形である。ガードが無くても `"" in JA_PUNCT` が真になるので結果は同じ (つまりガードを外してもテストは通る)。ここで固定しているのは分岐の有無ではなく、**空側に空白を入れない**という結合点の振る舞いそのものである。
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

        リスト項目の数は変わらず、段落テキストの比較は空白を無視するので、既存の2条件はどちらもこれを素通りする。
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

    ここが壊れると「変更なし・失敗 0」と出て成功に見える。unwrap_text と verify のテストはこの壊れ方を一切守らない。
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

    def test_warns_when_the_ast_parser_is_missing(self):
        """**黙って飛ばさない。** 検証が 1 つ欠けたまま成功に見えるのが最も危ない形である。"""
        self._write("notes/a.md")
        saved = unwrap._MarkdownIt, unwrap.HAS_AST_PARSER
        unwrap._MarkdownIt, unwrap.HAS_AST_PARSER = None, False
        try:
            code, output = _run_main([str(self.tmp)])
        finally:
            unwrap._MarkdownIt, unwrap.HAS_AST_PARSER = saved
        self.assertEqual(code, 0)
        self.assertIn("警告: markdown-it-py が無いため", output)

    def test_does_not_warn_when_the_ast_parser_is_present(self):
        self._write("notes/a.md")
        code, output = _run_main([str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertEqual("markdown-it-py が無い" in output,
                         not unwrap.HAS_AST_PARSER)

    def test_lists_odd_join_points_in_a_dry_run(self):
        """**適用時と dry-run の両方で出す。** dry-run でこそ見たい情報である。"""
        path = self.tmp / "notes" / "a.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("本文が折り返されて\n$$ x $$\n", encoding="utf-8")
        code, output = _run_main([str(self.tmp)])
        self.assertEqual(code, 0)
        self.assertIn("未知の結合点", output)
        self.assertIn(str(path), output)
        self.assertEqual(path.read_text(encoding="utf-8"),
                         "本文が折り返されて\n$$ x $$\n")

    def test_a_target_inside_a_worktree_is_not_skipped(self):
        """対象ディレクトリ自身が .claude/worktrees/ の下にあっても除外しない。

        除外は対象ディレクトリからの相対で判定する。絶対パスで判定すると worktree の中で走らせた瞬間に全件が除外され、「変更なし・失敗 0」と出て成功に見える。
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

        接頭辞 `"/.claude/worktrees/"` で判定していたときは、対象を `<repo>/.claude` にすると相対パスが `/worktrees/...` になって一致せず、**進行中の別ブランチの worktree を書き換えていた**。
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

        片方だけが数えると、変換しないと決めた場所の折り返しが残量に出て、直し切れない数がいつまでも残る。
        """
        self.assertEqual(measure_wraps.SKIP_PARTS, unwrap.SKIP_PARTS)

    def test_the_sentence_end_pattern_matches_unwrap(self):
        """文末の定義も2つのファイルで同じであること。

        片方だけが文末を折り返しと見なすと、結合しないと決めた改行が残量に出て、直し切れない数がいつまでも残る。
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


class TestHtmlBlocks(unittest.TestCase):
    """HTML ブロックの中は触らない。

    markdown では `<!--` から `-->` までのコメントや、ブロックレベルのタグで始まる領域は HTML ブロックであり、中身はそのまま出力される。結合すると閉じの `-->` が箇条書きの項目にくっつき、`<div>` のようなタグでは構造が壊れる。
    **この壊れ方は verify の3条件 (当時) をすべてすり抜けた。** フェンスの欠陥と同じで、文字は欠けず、構造の数も変わらず、段落の頭のインデントも変わらないからである。いまは第4条件 (マーカーだけの行) がこの形を検出する (TestVerifyMarkerLines を見よ) が、それは二重の網であって、ブロックの認識が正しいことの代わりではない。
    """

    def test_a_multi_line_html_comment_is_not_joined(self):
        """テンプレートで実際に壊れた形をそのまま固定する。"""
        src = ("<!--\n"
               "執筆者チェックリスト:\n"
               "- [ ] タイトル55〜60文字以内\n"
               "- [ ] Notionログからの具体的エピソード\n"
               "-->\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_the_closing_marker_is_not_joined_to_the_previous_line(self):
        src = "<!--\nコメントの本文である\n-->\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_an_unclosed_html_comment_runs_to_the_end_of_the_file(self):
        src = "<!--\n閉じの無いコメントが\n続いたまま終わる\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_single_line_html_comment_closes_on_its_own_line(self):
        """`<!-- ... -->` は 1 行で閉じる。閉じたことを見落とすと、後続の本文まで飲み込む。"""
        src = "<!-- 一行のコメント -->\n\n本文が折り\n返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "<!-- 一行のコメント -->\n\n本文が折り返されている。\n")

    def test_a_block_level_tag_region_is_not_joined_until_a_blank_line(self):
        src = ("<div class=\"note\">\n"
               "中の行が折り\n"
               "返されている\n"
               "</div>\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        self.assertEqual(unwrap.unwrap_text(src),
                         src.replace("本文が折り\n返されている。",
                                     "本文が折り返されている。"))

    def test_a_comment_inside_a_code_fence_does_not_open_an_html_block(self):
        """フェンスの中の `<!--` はフェンスの中身である。順序を誤ると、フェンスが閉じたあとの本文まで HTML ブロックとして扱われる。"""
        src = ("```html\n"
               "<!--\n"
               "```\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        self.assertEqual(unwrap.unwrap_text(src),
                         src.replace("本文が折り\n返されている。",
                                     "本文が折り返されている。"))

    def test_an_inline_comment_does_not_open_an_html_block(self):
        """行の途中の `<!--` は段落の一部であって HTML ブロックではない。"""
        src = "本文の途中に <!-- 注記 --> が\n入っている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "本文の途中に <!-- 注記 --> が入っている。\n")

    def test_an_autolink_does_not_open_an_html_block(self):
        """`<https://…>` はタグ名の形ではないので HTML ブロックを開かない。"""
        src = "<https://example.com> を参照\nすること。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "<https://example.com> を参照すること。\n")

    def test_an_html_block_interrupts_a_paragraph(self):
        """段落の続きに見える位置の `<!--` でも、そこで切って触らない。"""
        src = "本文である\n<!--\nコメントの中\n-->\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_the_html_block_handling_matches_unwrap(self):
        """unwrap.py と measure_wraps.py の HTML ブロックの扱いが一致する。"""
        lines = ["<!--", "-->", "<!-- 一行 -->", "  <!--", "    <!--",
                 "<div>", "<div class=\"x\">", "</div>", "<br/>", "<hr />",
                 "<https://example.com>", "<型引数>", "本文 <!-- 注記 -->",
                 "本文", "", "   <span>", "<x-custom>", "<1tag>", "<!DOCTYPE>",
                 "<pre>", "<PRE>", "</pre>", "<pre class=\"x\">",
                 "<script>", "</script>", "<style>", "</style>",
                 "<textarea>", "</textarea>", "<pre>コード</pre>",
                 "<prefix>", "<presentation class=\"x\">"]
        for line in lines:
            self.assertEqual(unwrap.html_block_open(line),
                             measure_wraps.html_block_open(line), line)
            for kind in ("comment", "raw", "tag"):
                self.assertEqual(unwrap.html_block_closes(line, kind),
                                 measure_wraps.html_block_closes(line, kind),
                                 (line, kind))

    def test_measure_does_not_count_wraps_inside_an_html_comment(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = pathlib.Path(tmp.name)
        (base / "a.md").write_text("<!--\n折り返された行が\nコメントの中にある\n-->\n",
                                   encoding="utf-8")
        self.assertEqual(measure_wraps.classify(base / "a.md"), (0, 0, 0))

    def test_measure_does_not_count_a_line_before_an_html_block_as_wrapped(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = pathlib.Path(tmp.name)
        (base / "a.md").write_text("本文である\n<!--\nコメント\n-->\n",
                                   encoding="utf-8")
        body, cont, _ = measure_wraps.classify(base / "a.md")
        self.assertEqual((body, cont), (1, 0))


class TestRawHtmlBlocks(unittest.TestCase):
    """CommonMark の HTML ブロックの 1 種目 (`<pre>` `<script>` `<style>` `<textarea>`) は空行では終わらない。

    この 4 つで始まるブロックだけは**閉じタグを含む行までが範囲**である。他の種別と同じ「空行まで」で扱うと、空行をまたいだ続きが本文として結合される。`<pre>` は空白が意味を持つので、結合すれば描画が変わる。
    実データには 0 件だが、**フェンスの欠陥と完全に同じ種類 (開閉の範囲の取り違え)** なので件数に関わらず塞ぐ。
    """

    def test_a_pre_block_is_not_joined_across_a_blank_line(self):
        src = ("<pre>\n"
               "最初の行\n"
               "\n"
               "続きの行が\n"
               "折り返されている\n"
               "</pre>\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_script_block_is_not_joined_across_a_blank_line(self):
        src = ("<script>\n"
               "// 説明が\n"
               "// 折り返されている\n"
               "\n"
               "// 空行の後も\n"
               "// 中身である\n"
               "</script>\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_a_style_block_is_not_joined_across_a_blank_line(self):
        src = ("<style>\n"
               "/* 説明が */\n"
               "\n"
               "/* 空行の後も */\n"
               "/* 中身である */\n"
               "</style>\n")
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_the_block_ends_at_the_closing_tag_and_the_body_after_it_is_joined(self):
        src = ("<pre>\n"
               "中身が\n"
               "\n"
               "ある\n"
               "</pre>\n"
               "\n"
               "本文が折り\n"
               "返されている。\n")
        self.assertEqual(unwrap.unwrap_text(src),
                         src.replace("本文が折り\n返されている。",
                                     "本文が折り返されている。"))

    def test_a_pre_block_closed_on_its_own_line_does_not_swallow_the_body(self):
        src = "<pre>コード</pre>\n\n本文が折り\n返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "<pre>コード</pre>\n\n本文が折り返されている。\n")

    def test_a_tag_whose_name_merely_starts_with_pre_is_an_ordinary_tag_block(self):
        """`<prefix>` は 1 種目ではない。タグ名の直後が空白・`>`・`/>`・行末のいずれかであることを見る。"""
        self.assertEqual(unwrap.html_block_open("<prefix>"), "tag")
        self.assertEqual(unwrap.html_block_open("<pre>"), "raw")

    def test_the_closing_tag_match_is_case_insensitive(self):
        src = "<PRE>\n中身が\n\nある\n</PRE>\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_an_unclosed_raw_block_runs_to_the_end_of_the_file(self):
        src = "<pre>\n閉じの無い中身が\n\n続いたまま終わる\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_measure_does_not_count_wraps_inside_a_pre_block(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = pathlib.Path(tmp.name)
        (base / "a.md").write_text(
            "<pre>\n最初の行\n\n続きの行が\n折り返されている\n</pre>\n",
            encoding="utf-8")
        self.assertEqual(measure_wraps.classify(base / "a.md"), (0, 0, 0))


class TestContainerDirectives(unittest.TestCase):
    """コンテナディレクティブ (`:::column` / `::::columns` / 閉じの `:::`) の行は本文ではない。

    適用先のリポジトリがプロダクトの記法としてこれを使っている。現時点で壊れていないのは、たまたま `:::column` の直後が見出しで段落が切れているからにすぎず、**日本語の段落の直後に閉じの `:::` が来た瞬間に本文として結合される**。しかも verify の 3 条件はこれをすべてすり抜ける。
    中身は普通の markdown の本文なので、**マーカーの行だけを触らない行として扱い、中の折り返しは結合する**。
    """

    def test_a_closing_directive_is_not_joined_to_the_paragraph_above(self):
        """レビューが挙げた再現入力をそのまま固定する。"""
        src = (":::column\n"
               "左のカラムの本文が\n"
               "折り返されている\n"
               ":::\n"
               "::::\n")
        self.assertEqual(unwrap.unwrap_text(src),
                         ":::column\n"
                         "左のカラムの本文が折り返されている\n"
                         ":::\n"
                         "::::\n")

    def test_an_opening_directive_does_not_join_the_line_below_it(self):
        src = "::::columns\n:::column\n本文が折り\n返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "::::columns\n:::column\n本文が折り返されている。\n")

    def test_the_body_inside_a_container_is_still_joined(self):
        """マーカーを触らないだけで、中身は普通の本文として結合する。フェンスのように「開いたら閉じるまで中身」にすると、カラムの中の折り返しが一切直らない。"""
        src = ("::::columns\n"
               ":::column\n"
               "### 左カラム\n"
               "\n"
               "説明の文が折り\n"
               "返されている。\n"
               ":::\n"
               "::::\n")
        self.assertEqual(unwrap.unwrap_text(src),
                         src.replace("説明の文が折り\n返されている。",
                                     "説明の文が折り返されている。"))

    def test_a_directive_indented_within_three_columns_is_still_a_directive(self):
        src = "本文である\n   :::\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_two_colons_are_not_a_directive(self):
        """コロン 2 個は本文である。広げすぎると普通の行を触らなくなる。"""
        self.assertIsNone(unwrap.DIRECTIVE.match("::だから"))
        self.assertTrue(unwrap.DIRECTIVE.match(":::"))

    def test_measure_does_not_count_a_line_before_a_closing_directive_as_wrapped(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = pathlib.Path(tmp.name)
        (base / "a.md").write_text(":::column\n本文である\n:::\n", encoding="utf-8")
        body, cont, _ = measure_wraps.classify(base / "a.md")
        self.assertEqual((body, cont), (1, 0))

    def test_the_block_start_judgement_matches_unwrap(self):
        """unwrap.py の is_block_start と measure_wraps.py の同名の判定が一致する。

        以前は `measure_wraps.BLOCK_START` が `===` を含み `***` `___` を含まず、unwrap.py と食い違っていた。片方だけが段落の境界をずらすと、直さないと決めた改行が残量に出たり、直したはずの改行が残量に出続けたりする。
        """
        lines = [":::", "::::columns", ":::column", "   :::", "    :::",
                 "::だから", "===", "==", "---", "----", "***", "___",
                 "*強調*", "_強調_", "- 項目", "1. 項目", "1) 項目", "-",
                 "# 見出し", "####### 七個", "> 引用", "| a | b |",
                 "```", "```ts", "~~~", "<!--", "<div>", "<pre>",
                 "本文である", "", "    インデント"]
        for line in lines:
            self.assertEqual(unwrap.is_block_start(line),
                             measure_wraps.is_block_start(line), line)


class TestVerifyMarkerLines(unittest.TestCase):
    """verify の第4条件: 英数字も CJK も含まない非空行は、変換後も同じ内容の独立した行として同じ数だけ存在する。

    1〜3 は「文字列としての md」の性質しか見ておらず、**ブロックの境界がどこにあるか**を一切参照しない。この道具が出した欠陥はどちらもまさにその情報を壊すものだった。第4条件は `unwrap` のブロックモデルに一切依存しない純粋に語彙的な不変量である。
    """

    def test_a_swallowed_html_comment_close_is_caught(self):
        """今回の HTML コメントの欠陥 (修正前の版の出力) がこの条件で捕まる。"""
        before = "<!--\n執筆者チェックリスト:\n- [ ] タイトル\n-->\n"
        after = "<!-- 執筆者チェックリスト:\n- [ ] タイトル -->\n"
        self.assertTrue(unwrap.verify(before, after))

    def test_a_swallowed_container_directive_is_caught(self):
        before = ":::column\n本文が\n折り返されている\n:::\n"
        after = ":::column 本文が折り返されている :::\n"
        self.assertTrue(unwrap.verify(before, after))

    def test_a_swallowed_math_delimiter_is_caught(self):
        before = "式の説明である\n$$\n"
        after = "式の説明である $$\n"
        self.assertTrue(unwrap.verify(before, after))

    def test_a_swallowed_setext_underline_is_caught(self):
        before = "見出しの文字列\n===\n"
        after = "見出しの文字列 ===\n"
        self.assertTrue(unwrap.verify(before, after))

    def test_a_swallowed_toml_fence_is_caught(self):
        before = "説明の文\n+++\n"
        after = "説明の文 +++\n"
        self.assertTrue(unwrap.verify(before, after))

    def test_an_ordinary_unwrap_is_not_a_false_positive(self):
        before = ":::column\n本文が\n折り返されている\n:::\n\n---\n"
        after = unwrap.unwrap_text(before)
        self.assertEqual(unwrap.verify(before, after), [])

    def test_a_line_containing_digits_is_not_a_marker_line(self):
        """英数字を含む行は対象外である。`::::columns` のような情報文字列つきの行もここに入らない。"""
        self.assertEqual(unwrap._marker_lines("::::columns\n:::\n"), [":::"])

    def test_the_fourth_condition_does_not_catch_a_collapsed_fence(self):
        """**限界の固定。** フェンスの欠陥と `<pre>` の欠陥は第4条件までのどれでも捕まらない。

        どちらもマーカーの行そのものは独立した行として全部残り、壊れるのはマーカーに挟まれた中身のほうだからである。第4条件は 3 条件の穴を**部分的に**塞ぐものであって、ブロックの認識が正しいことの代わりにはならない。この事実を知らずに第4条件を信頼すると、同じ種類の欠陥をまた通す。捕まえるのは第5条件 (AST 比較) である (`TestVerifyAst` を見よ)。
        """
        before = "```\nconst a = 1\nconst b = 2\n```\n"
        after = "```\nconst a = 1 const b = 2\n```\n"
        self.assertEqual(unwrap._squeeze(before), unwrap._squeeze(after))
        self.assertEqual(unwrap._marker_lines(before),
                         unwrap._marker_lines(after))
        self.assertEqual(unwrap._paragraph_indents(before),
                         unwrap._paragraph_indents(after))
        for _, pattern in unwrap.STRUCTURE:
            self.assertEqual(unwrap._count(before, pattern),
                             unwrap._count(after, pattern))


@unittest.skipUnless(unwrap.HAS_AST_PARSER, "markdown-it-py が無い")
class TestVerifyAst(unittest.TestCase):
    """検証の第5条件。独立したパーサ (markdown-it-py) で見たブロックの列を突き合わせる。"""

    def test_catches_a_collapsed_fence_that_the_first_four_conditions_miss(self):
        """**この検査の存在理由。** 第4条件までが素通りさせるフェンスの欠陥を捕まえる。"""
        before = "```\nconst a = 1\nconst b = 2\n```\n"
        after = "```\nconst a = 1 const b = 2\n```\n"
        self.assertEqual(
            unwrap.ast_problems(before, after),
            ["独立したパーサで見たブロックの列が変わった: "
             "1 番目のブロック (fence) の中身が変わった"])

    def test_catches_a_collapsed_pre_block(self):
        """HTML ブロックの 1 種目 (`<pre>`) の欠陥も、第4条件までは素通りする。"""
        before = "<pre>\nline one\nline two\n</pre>\n"
        after = "<pre>\nline one line two\n</pre>\n"
        self.assertEqual(unwrap._marker_lines(before),
                         unwrap._marker_lines(after))
        self.assertTrue(unwrap.ast_problems(before, after))

    def test_catches_a_paragraph_swallowing_a_block_boundary(self):
        """ブロックの境界が動いたことを、ブロックの種別の違いとして見る。"""
        before = "本文である\n\n> 引用である\n"
        after = "本文である > 引用である\n"
        self.assertTrue(unwrap.ast_problems(before, after))

    def test_does_not_flag_removing_a_newline_inside_a_paragraph(self):
        """**段落内の改行の除去は正当な変化である。** 差と見なしてはならない。"""
        before = "日本語の本文が桁数で\n折り返されている\n"
        self.assertEqual(unwrap.ast_problems(before, unwrap.unwrap_text(before)),
                         [])

    def test_does_not_flag_the_space_inserted_at_a_join(self):
        before = "設計は Claude\nCode の上で動く\n"
        self.assertEqual(unwrap.ast_problems(before, unwrap.unwrap_text(before)),
                         [])

    def test_normalisation_stays_inside_a_block(self):
        """**第1条件との決定的な差。** 文が別のブロックに移っても、squeeze では見えない。"""
        before = "# 見出しである\n\n本文である\n"
        after = "# 見出しである本文である\n"
        self.assertEqual(unwrap._squeeze(before), unwrap._squeeze(after))
        self.assertTrue(unwrap.ast_problems(before, after))

    def test_reports_a_missing_parser_instead_of_failing(self):
        """パーサが無い環境では検査を行わず、空のリストを返す。

        黙って飛ばさないための文言は `AST_MISSING_NOTE` にあり、main が出す (`TestMain` を見よ)。
        """
        saved = unwrap._MarkdownIt
        unwrap._MarkdownIt = None
        try:
            self.assertIsNone(unwrap.ast_blocks("本文\n"))
            self.assertEqual(unwrap.ast_problems("```\na\nb\n```\n",
                                                 "```\na b\n```\n"), [])
        finally:
            unwrap._MarkdownIt = saved


class TestVerifyWiring(unittest.TestCase):
    """**5つの条件が `verify()` に配線されていること**そのものを固定する。

    条件ごとの検査は上のクラスが押さえているが、そこでは `ast_problems` のように**検査そのものを直接呼んで**いるものがある。直接呼ぶだけだと、`verify()` からその行を削っても全部のテストが通る —— 検証が 1 つ欠けたまま「成功」に見える形であり、この道具が最も警戒してきたものである。実際、第5条件を `verify()` から削る変異は 139 件のテストを全部すり抜けた。

    そこでここでは**必ず `verify()` を呼び**、返るリストを丸ごと突き合わせる。件の条件だけが当たる入力を使い、期待値を完全一致で書くので、どれか 1 つの配線が外れればその 1 つのテストだけが落ちる。

    AST 比較はパーサが無い環境では働かないので、第1〜4条件の期待値からは AST の 1 行を除いて比べる (その 1 行自体は下の第5条件のテストが押さえる)。
    """

    AST_PREFIX = "独立したパーサで見たブロックの列が変わった"

    def without_ast(self, problems):
        return [p for p in problems if not p.startswith(self.AST_PREFIX)]

    def test_the_first_condition_is_wired(self):
        """第1条件 (段落テキストの一致) が verify から呼ばれている。"""
        before = "日本語の本文が桁数で\n折り返されている。\n"
        after = "日本語の本文が桁数で\n"
        self.assertEqual(
            self.without_ast(unwrap.verify(before, after)),
            ["段落テキストが一致しない (文字の欠落・重複・順序変更)"])

    def test_the_second_condition_is_wired(self):
        """第2条件 (構造の数の不変) が verify から呼ばれている。"""
        before = "## 見出し\n\n本文である。\n"
        after = "見出し\n\n本文である。\n"
        self.assertIn("見出し の数が 1 から 0 に変わった",
                      unwrap.verify(before, after))

    def test_the_third_condition_is_wired(self):
        """第3条件 (段落の頭のインデントの並び) が verify から呼ばれている。"""
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
        self.assertEqual(self.without_ast(unwrap.verify(before, after)),
                         ["段落の頭のインデントの並びが変わった"])

    def test_the_fourth_condition_is_wired(self):
        """第4条件 (マーカーだけの行) が verify から呼ばれている。

        コンテナディレクティブ (`:::`) は CommonMark には無いので、AST から見ればただの段落である。第4条件を外すとこの壊れ方は 5 条件すべてを通る。
        """
        before = ":::column\n本文が\n折り返されている\n:::\n"
        after = ":::column 本文が折り返されている :::\n"
        self.assertEqual(
            unwrap.verify(before, after),
            ["マーカーだけの行 (英数字も CJK も含まない非空行) の並びが変わった: "
             "1 行から 0 行"])

    @unittest.skipUnless(unwrap.HAS_AST_PARSER, "markdown-it-py が無い")
    def test_the_fifth_condition_is_wired(self):
        """第5条件 (AST 比較) が verify から呼ばれている。

        **潰れたフェンスは第1〜4条件のどれにも当たらない** (`test_the_fourth_condition_does_not_catch_a_collapsed_fence`)。だから `verify()` がこの見本に対して非空を返すことは、第5条件が配線されていることと同値である。この 1 行を `verify()` から削る変異は、このテストが入るまで 139 件のテストを全部通っていた。
        """
        before = "```\nconst a = 1\nconst b = 2\n```\n"
        after = "```\nconst a = 1 const b = 2\n```\n"
        self.assertEqual(
            unwrap.verify(before, after),
            ["独立したパーサで見たブロックの列が変わった: "
             "1 番目のブロック (fence) の中身が変わった"])

    def test_a_clean_unwrap_passes_every_condition(self):
        """5 条件すべてが働いたうえで、正当な変換は素通りする (誤検出が無い)。"""
        before = ("# 見出し\n"
                  "\n"
                  "- 箇条書きの項目が桁数で\n"
                  "  折り返されている。\n"
                  "\n"
                  ":::column\n"
                  "本文が桁数で\n"
                  "折り返されている\n"
                  ":::\n"
                  "\n"
                  "```ts\n"
                  "const a = 1\n"
                  "```\n")
        self.assertEqual(unwrap.verify(before, unwrap.unwrap_text(before)), [])


class TestOddJoins(unittest.TestCase):
    """未知の結合点の一覧。検証が全部通っても、見たことのない形は人間に見せる。"""

    def test_reports_a_join_with_a_non_japanese_non_alnum_side(self):
        joins = []
        unwrap.join_parts(["本文である", "-->"], joins)
        self.assertEqual(joins, ["-->"])

    def test_reports_the_offending_side_when_it_is_on_the_left(self):
        joins = []
        unwrap.join_parts(["const a = 1;", "const b = 2;"], joins)
        self.assertEqual(joins, ["1;"])

    def test_does_not_report_an_ordinary_japanese_join(self):
        joins = []
        unwrap.join_parts(["日本語の本文が", "折り返されている"], joins)
        self.assertEqual(joins, [])

    def test_does_not_report_a_japanese_to_ascii_join(self):
        joins = []
        unwrap.join_parts(["この規約は", "CLAUDE.md に置く"], joins)
        self.assertEqual(joins, [])

    def test_does_not_report_a_join_at_full_width_punctuation(self):
        joins = []
        unwrap.join_parts(["本文であり、", "続きである"], joins)
        self.assertEqual(joins, [])

    def test_unwrap_text_collects_joins(self):
        joins = []
        unwrap.unwrap_text(":::column\n本文が\n折り返されている\n:::\n", joins)
        self.assertEqual(joins, [])

    def test_ignores_inline_markdown_markup_at_the_boundary(self):
        """**強調とコードスパンは普通の本文である。** 剥がさないと一覧が飾りで埋まる。

        剥がさずに実測したところ fde で 2,101 件・1,600 形が出て、先頭は `` `document/010-…` `` のようなただのコードスパンだった。読まれない一覧は無いのと同じである。
        """
        joins = []
        unwrap.join_parts(["本文である", "`document/010-outbound.md` を見よ"], joins)
        unwrap.join_parts(["本文である", "**強調した語**である"], joins)
        unwrap.join_parts(["`code`", "本文である"], joins)
        self.assertEqual(joins, [])

    def test_still_reports_an_html_tag_at_the_boundary(self):
        """**`<` と `>` は剥がさない。** HTML のタグはまさに見たい形だからである。"""
        joins = []
        unwrap.join_parts(["本文である", "<div>"], joins)
        self.assertEqual(joins, ["<div>"])

    def test_does_not_report_symbols_that_are_ordinary_in_japanese_prose(self):
        """`——`・`→`・`①`・`§` は日本語の技術文書の本文に普通に出る。"""
        joins = []
        for right in ["——である", "→ 次の段", "①である", "§4 を見よ"]:
            unwrap.join_parts(["本文である", right], joins)
        self.assertEqual(joins, [])

    def test_does_not_report_a_slash_or_a_dot(self):
        """`/` と `.` は一覧のノイズの最上位だった。

        `~/Joifup` 全体の 999 件 / 495 形のうち `/` が 317 件 (32%) を占め、実体は列挙の行末と**記号で始まるコードスパン**で、全部本文だった。
        """
        joins = []
        for left, right in [("`brainstorming` /", "`writing-plans`"),
                            ("本文である", "/ 次の要素"),
                            ("本文である", "`.gitignore` を見よ"),
                            ("本文である", ".uat-evidence/ に置く")]:
            unwrap.join_parts([left, right], joins)
        self.assertEqual(joins, [])

    def test_still_reports_block_markers_after_adding_the_slash_and_the_dot(self):
        """**足してもブロックの境界は見える。** どのマーカーも `/` や `.` を含まない。"""
        for right in ["-->", "</div>", ":::", "$$", "===", "+++"]:
            joins = []
            unwrap.join_parts(["本文である", right], joins)
            self.assertEqual(joins, [right], right)

    def test_still_reports_box_drawing(self):
        """**罫線は足さない。** フェンスの外の木構造図が結合されている印だからである。"""
        joins = []
        unwrap.join_parts(["tools/", "├── workflow/"], joins)
        self.assertEqual(joins, ["├──"])

    def test_truncates_a_long_sample(self):
        joins = []
        unwrap.join_parts(["本文である", "-" * 100], joins)
        self.assertEqual(len(joins[0]), unwrap.JOIN_SAMPLE_MAX)

    def test_groups_the_same_shape_into_one_line(self):
        import collections
        lines = []
        counts = collections.Counter({"-->": 20, ":::": 3})
        unwrap.report_odd_joins(counts, {"-->": "a.md", ":::": "b.md"},
                                lines.append)
        body = "\n".join(lines)
        self.assertIn("23 件 / 2 形", body)
        self.assertIn("20  '-->' との結合", body)
        self.assertEqual(len([l for l in lines if "との結合" in l]), 2)

    def test_says_nothing_when_there_is_nothing_to_say(self):
        import collections
        lines = []
        unwrap.report_odd_joins(collections.Counter(), {}, lines.append)
        self.assertEqual(lines, [])


if __name__ == "__main__":
    unittest.main()
