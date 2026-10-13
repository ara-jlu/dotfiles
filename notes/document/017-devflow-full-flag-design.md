---
title: j-devflow の Phase B を既定と `-full` に組み替える
tag: [document]
Project: devops
Task: 017-devflow-light-by-default
created_at: 2026-10-13
updated_at: 2026-10-13
---

# j-devflow の Phase B を既定と `-full` に組み替える

## 背景と問題

`j-devflow` の Phase B は、既定が full（タスク毎に `task-reviewer`）で、`-light` を付けたときだけタスク毎レビューを落とす。2026-10-02、`tasks/016`（Phase A の設計書に fresh なレビューを入れる）の対話で、前段が厚くなるなら実装のタスク毎レビューは既定で要らないのではないか、と依頼者が提起した。

既定を逆にするだけでは足りない問題が2つある。

- **判定の材料が薄い。** `-light` にするかは、dispatch する PM が起票時のタスク本文から決めている。joifup の `references/incidents.md` §2.4 の失敗例（2026-08-15、joifup tasks/208）では、本文が `sanitizeSidebarSections` を名指ししていたのに light で出し、実装が進んでからエスカレーション条件が発火した。概要レベルの本文だけで判定すると、こうした見落としが起きる。
- **最終レビューに計画が要件として示されない。** `j-devflow/SKILL.md` 手順 8 は「**diff だけ**を渡して」と書く。計画のファイルは手順 6 で同じブランチに commit されるので diff には含まれるが、照らし合わせる要件としては指定されていない。SDD 本来の最終レビューのテンプレート（superpowers `requesting-code-review/code-reviewer.md`）は `[PLAN_OR_REQUIREMENTS]` を受け取り、Plan alignment を見る。タスク毎レビューを既定で絞ると spec 準拠の検査は最終レビューが本体になるので、ここを要件として渡さないと検査が抜ける。

## 根拠（実測）

- **joifup tasks/008 の followup（task 195、各条件 2 反復）:** レビューを行った側だけが唯一の critical な退行を生み、タスク毎・最終の両方のレビュー層がそれを見逃した。タスク毎レビューなしの側は中核要件について正しいままだった。重要な正しさの網は SDD の「タスク毎に fresh subagent」の隔離だった。
- **joifup の 2026-08-14〜15 の運用（light 2 件 / full 14 件）:** タスク毎レビューの層が拾った欠陥は 0 件。価値のある発見（201 の相互マスク・202 の 100ms 遅延・203 の解決済み検証・217 の停止性）はすべてブランチ全体の最終レビューの層が拾った。
- **016 の前段の厚み:** 設計書は GATE 1 の前に fresh なレビューを通るようになった。設計書の穴は Phase B のどのレビューでも捕まらないので、前段で捕まえる層が増えた分、後段の早期検出の層を削る余地が広がった。

どちらの実測も n は小さい。よって directional として扱い、全タスクにタスク毎レビューを戻す `-full` を残す。

## 決定事項

### 1. Phase B のレビューの層

`-light` という概念は廃止し、Phase B は「既定」と「`-full`」の2つにする。

| | 既定 | `-full` |
|---|---|---|
| タスク毎に fresh subagent（SDD の隔離） | あり | あり |
| タスク毎の `task-reviewer` | 該当タスクだけ | 全タスク |
| タスク毎の `ecc:security-reviewer` | 該当タスクだけ | 該当タスクだけ |
| ブランチ全体の最終レビュー | あり | あり |

**該当の区分（定義は CLAUDE.md の1箇所に置く）:** 次のどれかに触れるタスクを該当とする。

- 信頼の境界を越えて値を受け取る、または出す経路（利用者の入力・外部のネットワーク・第三者が書ける内容から受け取る、それを HTML・シェル・SQL などに出す）。検証や無害化の有無は問わない（検証を書き忘れた新しい経路こそ拾う）。自前のプロセス間の受け渡しや、自リポジトリが管理するファイルを読むだけの経路は含めない
- 認証・認可
- 秘密（鍵・トークン・資格情報）
- 外部に公開する API の契約（ルート・引数・応答の形）。リポジトリの内部だけで呼ぶ関数は含めない
- 機微データ（個人情報・顧客データ）の読み書き

**リポジトリ固有の手掛かり:** 手掛かりは区分を広げる。手掛かりに当たるタスクは、上の5項目に当たらなくても該当とする（リポジトリで事故の重い箇所を、汎用の区分の外でも拾うため）。手掛かりはファイルや関数の名前の形で書く（joifup なら `sanitize*`・`*-href`・検証系・daemon の公開ルート・書き込み経路の fail-closed ガード）は、そのリポジトリの `CLAUDE.md` に置く。j-devflow はリポジトリ共通なので固有の名前を持たない。`CLAUDE.md` はセッションに自動で載るので、判定する orchestrator は追加の手順なしにそれを読める。

**該当タスクの判定:** 手順 7 の冒頭で、orchestrator が永続化された計画の各タスクを読み、上の区分と手掛かりで判定する。superpowers の計画はタスク毎に触るファイルを列挙するので、それを材料にする。判定結果は SDD の progress ledger のヘッダに `<WT>` と並べて記録する。writing-plans には何も注入しない（計画を読む側で判定する。ラップしないため）。判定の材料が「起票時の概要」から「GATE 1 を通った設計と計画」に変わるので、208 型の見落としが起きにくくなる。

**判定が外れたとき:** タスク毎レビューを入れなかったタスクが完了するたびに、orchestrator は `git diff --name-only <base>..<head>` でそのタスクが触ったファイルの名前だけを見て、区分と手掛かりに当たるかを確かめる。出力は数行のファイル名で、diff の本文は orchestrator のコンテキストに入れないので、SDD のファイルでの受け渡しの規則に反しない。当たれば、次のタスクに進む前に、そのタスクに `task-reviewer` と `ecc:security-reviewer` を dispatch する（停止して問わない。判定が直るだけで、人間に仰ぐ判断が無い）。ledger にそのタスクの完了を書くのは、この確かめ（と、当たったときのレビュー）が済んでからにする。先に `complete` と書くと、確かめの途中で圧縮が入ったときに SDD の再開の規則がそのタスクを飛ばす。SDD が BLOCKED への対処として計画のタスクを分けたときは、新しくできたタスクも判定し直す。後続のタスクが積み上がる前に入れるので、旧 `-light` で問題になった「実装が進んでからの発火」にはならない。ファイル名に現れない外れは、最終レビューで拾う（ブランチの diff が区分に触れれば `ecc:security-reviewer` を dispatch する既存の規則）。

**progress ledger の記録:** タスク毎レビューを入れなかったタスクは `Task N: complete (commits <base7>..<head7>, per-task review: none)` と記録する。SDD の形式に合わせて範囲で残し、`review clean` は流用しない。コンパクション後の再開で、レビュー済みと誤読しないためである。この記録規則は j-devflow の外の SDD にも効くよう、CLAUDE.md に置く（節 2）。

**停止して dispatcher に問う条件（両モード共通）:** 設計に無かったスキーマ変更・データ移行・削除・セキュリティや認証のポリシーの変更・公開 API の契約変更が必要だと判明した場合。`-auto` のエスカレーション条件の「不可逆で影響範囲が大きい」区分と同じである。旧 `-light` にあった「スコープが想定を超えて広がった」は削る。これは「light で足りる」という前提が崩れたことへの対処だったので要らない。旧 `-light` にあった「最終レビューが Critical/Important を返す」は、fix ループを通常どおり回すという注記にすぎなかったので削る。

**`-light` フラグ:** 廃止する。互換の受け付けは置かない。`-auto`・`-full` 以外のフラグ（廃止したフラグを含む）を付けて起動されたら、推測で読み替えず、停止して dispatcher に問う。SKILL.md には廃止したフラグの名前を書かない（受け入れ基準の grep と衝突させないため。経緯はこの設計書にある）。

### 2. 最終レビューに渡すもの（手順 8）と CLAUDE.md

**手順 8:** 受け手ごとに書き分ける。

- **SDD の最終 code-reviewer（spec 準拠）:** review-package と、永続化された計画のパスを `[PLAN_OR_REQUIREMENTS]` として渡す。superpowers 本来の挙動に合わせるだけの変更である。
- **`ecc:<lang>-reviewer` と `ecc:security-reviewer`（品質・セキュリティ）:** review-package だけを渡し、diff に集中させる。CLAUDE.md の「Spec準拠 = superpowers、品質 = ECC」の分担を崩さない。
- どの受け手にも、実装した subagent と orchestrator の会話は絶対に渡さない。

**dotfiles の `.claude/CLAUDE.md`:** `~/.claude/CLAUDE.md` から symlink されているので、全リポジトリの SDD に効く。この規則を j-devflow の中だけに閉じず、SDD の使い方全般の規則にする。

- 「最終 whole-branch レビュー」の項に、SDD の最終 code-reviewer には計画も要件として渡すことを足す。
- 「差分が auth / 入力 / 秘密 / API / 機微データに触れる場合は `ecc:security-reviewer` も dispatch」の行は、区分を自前で列挙せず、新しい定義を指す形に書き換える。最終レビューとタスク毎の判定が同じ物差しで動くようにするためである。
- 「タスク毎レビューは superpowers task-reviewer を維持し…」を書き換える。新しい内容は「タスク毎レビュー（task-reviewer と `ecc:security-reviewer`）は、計画を読んで該当と判定したタスクにだけ入れる。区分は上の定義。全タスクに入れるのは、依頼者が求めたとき（j-devflow では `-full`）」とする。区分の定義と、判定の外れの確かめ方（節 1）と、ledger の記録規則（節 1）はここに1箇所だけ置き、j-devflow はここを指す。
- これにより、j-devflow を通さずに SDD を起動した場合も、同じ判定で動く。判定するのは常に SDD の orchestrator である。

### 3. j-devflow/SKILL.md の他の箇所

- **モード節:** 見出しを「Phase B: 既定 vs `-full`」にし、節 1 の表の内容を書く。区分の定義は CLAUDE.md を指す。「`-light` が安全である理由」は「既定でタスク毎レビューを絞る理由」として数行に縮め、根拠はこの設計書へのポインタにする（`.claude/rules/comment-rationale.md` の一次情報は1箇所の規則。016 と同じ書き方）。
- **組み合わせの記述:** `-light -auto` を前提にした文を削る。起動例は `/j-devflow <id>`・`-auto`・`-full`・`-full -auto` にする。
- **判定の主体:** 「どのタスクを `-light` にするかは PM が決める」を、「タスク毎レビューを入れるタスクは j-devflow の orchestrator が計画から決める。`-full` を付けるかは dispatcher が起動時に決める」に直す。
- **手順 7 と手順 8・ガード・よくある失敗:** `-light` の分岐と記述を節 1・節 2 に合わせて書き直す。よくある失敗の「旧 inline の `-light` を復活させる」は削り、「最終レビューに計画を要件として渡さない」と「該当の判定を writing-plans への注入で済ませる（ラップ）」を足す。
- **`.claude/rules/skill-language.md`:** 識別子の例に挙げた `-light` を `-full` に差し替える。

### 4. joifup 側の追随

- **`CLAUDE.md`（joifup のリポジトリ直下）:** 節 1 の「リポジトリ固有の手掛かり」を短い節として足す。中身は incidents.md §2.4 に記録されている `sanitize*`・`*-href`・検証系・daemon の公開ルート・書き込み経路の fail-closed ガードである。incidents.md 側の記録は残す（写しではなく、生きた手掛かりの置き場所を CLAUDE.md に定める）。
- **`.claude/skills/joifup-pm/SKILL.md`:** 「`-light` の可否」を「`-full` の可否」にする。内容は「既定で足りる。タスク毎レビューを入れるかは j-devflow が計画から判定する。`-full` は、原因が特定できていないデバッグや UX の設計面が残るなど、全タスクを念のため見たいときだけ。迷ったら既定」。
- **`.claude/skills/joifup-pm/references/incidents.md`:** 書き換えない。このファイルは確定のもとになった事故を保存する読み物で、生きた手順は SKILL.md にある（incidents.md 1〜7 行、joifup-pm/SKILL.md 8 行）。§2.4 の冒頭に「`-light` は dotfiles の tasks/017 で廃止した。現行の判断は SKILL.md の `-full` の可否」という注記を1行だけ足す。208 の失敗例と 2026-08 の実測は、そのまま記録として残す。

## このタスクの進め方（2 リポジトリ）

j-devflow の Worktree 固定の契約・review-package・`j-finish` は、どれも 1 リポジトリを前提にしている。このタスクは dotfiles と joifup の両方を直すので、この1回に限って次のように進める。j-devflow 自体を複数リポジトリ対応に広げることはしない（YAGNI）。

- **worktree を2つ持つ:** dotfiles は手順 2 の `<WT>`。joifup は Phase B の開始時に、joifup の慣行どおり `.claude/worktrees/` の下に `git worktree add` で worktree を作り、その絶対ルートを `<WT_JOIFUP>` として ledger のヘッダに記録する。ブランチ名は `chore-dotfiles-017-devflow-full-flag` とする。joifup に Task は無いので、CLAUDE.md の「ブランチに Task の id を入れる」の代わりに、出どころの dotfiles の 017 を名前に入れる。
- **操作できることを最初に確かめる:** このセッションは dotfiles の worktree に固定されている。設計の時点で、joifup への git の読み取りは通ることを確かめた（固定は同じリポジトリの主チェックアウトへの操作を拒むもので、別のリポジトリは対象外と見られる）。書き込み（`git worktree add`・commit・push）は Phase B の最初の操作として確かめる。joifup に commit するのは SDD の implementer の subagent なので、orchestrator からだけでなく、subagent からの書き込み（`<WT_JOIFUP>` での空でない commit を1つ試し、その後に取り消す）でも確かめる。拒否されたら、joifup 側の計画のタスクを止め、joifup のルートで起動する別のセッションに、計画の joifup 側のタスクと `j-pr` を切り出す。dotfiles 側はそのまま進める。この場合、両方を1回で見る最終レビューは、後から終わる側のセッションで、両リポジトリの review-package と計画を合わせて行う。
- **計画のタスクはリポジトリごとに分ける:** 1つのタスクが両方のリポジトリを触らないようにする。各タスクの dispatch は、そのタスクのリポジトリの root に固定する（Worktree 固定の契約の (a)〜(c) を、`<WT>` を `<WT_JOIFUP>` に読み替えて適用する。assert も緩めない）。
- **最終レビューは1回で両方を見る:** review-package をリポジトリごとに作り、両方のパスと計画を同じ最終レビューに渡す。片方だけ直って片方が古いまま、という食い違いを見るのが目的なので、別々のレビューにしない。
- **PR を2本出す:** dotfiles は `j-finish`（Task 017 を In review に移す）、joifup は `j-pr`（house-style の PR 本文だけ。joifup に Task は起票しないので status は触らない）。両方の PR 本文で互いを参照する。
- **反映の時点:** `~/.claude/skills` と `~/.claude/CLAUDE.md` は dotfiles の主チェックアウトへの symlink なので、j-devflow の変更が効くのはマージして dotfiles のローカルの main を更新した時点である。joifup-pm も joifup のローカルの main を更新した時点で効く。両方の PR 本文に「2本ともマージし、両方のローカルの main を更新してから、次の j-devflow を起動する」と書く。

## 採らなかった案

- **既定を反転するだけ（`-full` を PM が起動時に決める）:** 変更は最小だが、判定がタスク本文だけに基づく構造が残り、208 型の見落としを防げない。
- **タスク毎レビューを廃止する（`-full` を持たない）:** 最も単純だが、根拠の実測の n が小さく、全タスクを見たいときに戻す手段が消える。
- **`-light` を互換として受け付け続ける:** dispatcher 側を同時に直すので要らない。意味の無いフラグを残すと、読む人がモードが3つあると誤解する。
- **判定の外れを最終レビューだけに預ける:** 根拠の実測は、区分に当たるタスクを full で出した後の数字で、区分に当たるのにタスク毎レビューが無かった場合を最終レビューがどれだけ拾うかは示していない。ファイル名だけを見る確かめ方は安いので、タスクの直後に入れる。
- **判定の外れを確かめるために orchestrator が diff の本文を読む:** SDD のファイルでの受け渡し（出力を orchestrator のコンテキストに入れない）に反する。ファイル名だけで足りる。
- **CLAUDE.md の規則を j-devflow の中だけに閉じる:** j-devflow を通さない SDD の扱いが別の規則になり、区分の定義が2箇所に分かれる。

## 受け入れ基準

- dotfiles の現役ファイル（`.claude/` 配下と `.claude/CLAUDE.md`。`.claude/worktrees/` の下は除く）と、joifup の `joifup-pm/SKILL.md` と `CLAUDE.md` に `-light` が残っていない。過去の `notes/`・`tasks/` と、joifup の `incidents.md`（保存用の記録）は対象外。
- `.claude/CLAUDE.md` に、該当の区分の定義・判定の外れの確かめ方・ledger の記録規則・タスク毎レビューの規則・最終 code-reviewer に計画を渡すことが、節 1・節 2 のとおりにある。最終レビューの `ecc:security-reviewer` の条件は、区分を自前で列挙せず定義を指している。
- `j-devflow/SKILL.md` に、`-full` の定義（節 1 の表の内容）・手順 7 の判定と ledger への記録・判定が外れたときの扱い・停止の条件・未知のフラグの扱い・手順 8 の受け手ごとの渡し方がある。区分の定義は CLAUDE.md を指し、写していない。
- joifup の `CLAUDE.md` に、リポジトリ固有の手掛かりがある。`joifup-pm/SKILL.md` の `-full` の可否が節 4 と一致する。`incidents.md` は §2.4 の注記1行だけが増えている。
- UI が無いので UAT は省く。確認は grep と通読で行う。
