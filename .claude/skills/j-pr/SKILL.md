---
name: j-pr
description: j-devflow の外で行った ad-hoc な開発の PR を開くときに使う — フルフローと同じ house-style の日本語 PR 本文だけを整え、フル終了処理（Joifup のステータス変更・承認タスク・Discord）は行わない。「PR だけ出したい」「house-style の PR 本文で開いて」「j-finish なしで PR を作って」に該当する場合に使う。
user-invocable: true
argument-hint: "[base-branch（既定: main）]"
---

# j-pr

## 概要

ad-hoc な作業に対して **house-style** の PR を開く — フルフローと同じ日本語 PR 本文を整え、他には何もしない。`j-devflow` を使わずに開発し、一貫した PR だけが必要なときに使う。

- **PR 本文** は `references/pr-body.md` の共通レシピに従う — `j-finish` も使う唯一の正典であり、両経路の本文を一致させる。
- **コミット** は CLAUDE.md の Git 節が既に規定している（英語・Semantic/Conventional・Atomic）— j-pr はコミットに触れない。
- **Joifup への副作用はない。** ステータス遷移・承認タスク・Discord は `j-finish`（実装完了後の終了処理）の役割。この作業に Joifup Task があり、フル終了処理を行いたい場合は `j-finish` を使う。

## 使う場面

- ad-hoc なブランチ → PR。j-devflow の背骨の外側で使う。
- マージには使わない。ステータス・承認・通知までの終了処理（それは `j-finish` の役割）にも使わない。

## 流れ

1. **Pre-flight**（読み取りのみ）: `git status --porcelain`（clean か？ dirty なら停止して報告する）、`git log <base>..HEAD --oneline`、`git diff --stat <base>...HEAD`。`<base>` = `$ARGUMENTS` または `main`。
2. **Push:** `git push -u origin <branch>`。
3. **PR 本文を書く** — `references/pr-body.md`（読むこと）に従い、一時 `.md` ファイルに出力する。各節を diff に根拠づける。この作業に関連する Joifup Task/plan があれば `## 関連` にその id/path を記載し、なければその行を省く。
4. **PR を作成する:** `gh pr create --base <base> --head <branch> --title "<type>: <日本語要約>" --body-file <tmp>.md`（依頼されていれば `--draft` を付ける）。
5. **PR に UI 変更が含まれる場合は UAT 証跡を添付する:** `python3 ~/.claude/skills/j-finish/scripts/uat_attach.py --evidence-dir .uat-evidence/<id> --pr <PR URL>` — 証跡コメントを投稿し、本文の `## UAT 証跡` 節（`references/pr-body.md` 参照）からリンクする。`gh >= 2.99.0` が必要。UI を含まない変更ではこの手順を省ける。
6. PR の URL を**報告する**。

## よくある失敗

- 旧 `/pr` スキルに手を伸ばす — それは Joifup ではなく Notion にリンクする。このレシピを使う。
- PR 本文を英語で書く、あるいはコミットを日本語で書く — PR 本文は日本語、コミットは英語（両者は独立している）。
- ここでステータス・承認・Discord を行う — それは `j-finish` の役割。
