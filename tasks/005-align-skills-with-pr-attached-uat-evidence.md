---
ID: TASK-458
Project: devops
created_at: '2026-09-05'
status: Done
title: UAT 証跡の PR 添付化に skill 側を合わせる
updated_at: '2026-09-05'
---

# UAT 証跡の PR 添付化に skill 側を合わせる

## 概要

joifup の tasks/295 で、UAT 証跡は `.uat-evidence/` に commit するのをやめ、`gh pr comment --attach` で PR に添付する形になった。`.uat-evidence/` は gitignore 済みで commit できない。

skill 側は旧運用のままで、**証跡を commit しろ・Files changed タブで見ろ**と指示し続けている。`j_finish.py` の「未 commit なら警告」も意味が反転している。`j-finish` / `j-devflow` / `j-pr` の 3 つ、計 7 箇所。

添付を実行する配線（証跡コメントの投稿、`gh` のバージョン確認）も未実装。

## 背景

skill は全プロジェクト共通なので、放置すると joifup 以外でも次の feature セッションが間違った手順を踏む。joifup 側だけ直った状態は、CLAUDE.md が禁じる「運用が二重になる状態」そのもの。
