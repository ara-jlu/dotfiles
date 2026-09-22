---
title: ハーネスを 2026-09 のベストプラクティスに照らして見直す
status: Not started
Project: devops
created_at: 2026-09-22
updated_at: 2026-09-22
---

# ハーネスを 2026-09 のベストプラクティスに照らして見直す

## 概要

`notes/research/015-claude-code-features-best-practices.md` の「結論・推奨」にある 5 つの見直し候補の優先順位を決め、個別に起票する。候補の一覧は同ノートが一次情報なので、ここには写さない。

## 背景

Claude 5 世代向けに Anthropic はシステムプロンプトの 80% を削り、「ルールより判断、手順より結果、前置きより progressive disclosure」へ方針を変えた。dotfiles のハーネスは 2025 の書き方で積み上がっているので、`006-harness-principles` の結論（少数原則）と整合させながら削る対象を決める必要がある。
