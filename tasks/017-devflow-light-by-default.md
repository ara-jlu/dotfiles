---
title: j-devflow の Phase B の既定を light にする
status: Not started
Project: devops
created_at: 2026-10-02
updated_at: 2026-10-02
---

# j-devflow の Phase B の既定を light にする

## 概要

`j-devflow` の Phase B は、既定が full（タスク毎レビューあり）で、`-light` を付けたときだけタスク毎レビューを落とす。これを逆にし、既定を light として、重要なタスクだけを明示して full で起動する形にするかどうかを決める。起動時に `-light` を選んでいる joifup リポジトリの `joifup-pm` の判断も、この変更に合わせる必要がある。

## 背景

2026-10-02、`tasks/016`（Phase A の設計書に fresh なレビューを入れる）の対話で、前段が厚くなるなら実装のタスク毎レビューは既定で要らないのではないか、と依頼者が提起した。

## 起票時のメモ（未検証）

- 出どころ: `tasks/016` の brainstorming（2026-10-02）。
- 材料: 008 followup（task 195、n=2、directional）で、タスク毎レビューは効いていなかったと記録されている（`j-devflow/SKILL.md` の「`-light` が安全である理由」）。
- 材料: SDD の最終レビューのテンプレート（superpowers `requesting-code-review/code-reviewer.md`）は `[PLAN_OR_REQUIREMENTS]` を受け取り、Plan alignment を見る。
- 危ないところ: `j-devflow/SKILL.md` 手順 8 の「**diff だけ**を渡して」は、字面では計画を渡さないとも読める。最終レビューに計画が渡らないと、brief からのずれの検査が消える。
- 危ないところ: `-light` の判断を持つのは joifup リポジトリの `.claude/skills/joifup-pm/SKILL.md` と `references/incidents.md`（リポジトリをまたぐ）。
- 決めることの候補: full を明示するフラグの名前（`-full` など）、既存の `-light` フラグの扱い、手順 8 の文言。
