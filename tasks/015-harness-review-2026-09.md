---
title: ハーネスを 2026-09 のベストプラクティスに照らして見直す
status: Not started
Project: devops
created_at: 2026-09-22
updated_at: 2026-09-22
---

# ハーネスを 2026-09 のベストプラクティスに照らして見直す

## 概要

`notes/research/015-claude-code-features-best-practices.md` の「結論・推奨」にある 5 つの見直し候補（CLAUDE.md の手順節を skill / rule へ移す、例外なしの規則を hook へ移す、自作 skill の description を短く具体的に、`/doctor` の実行、半年ごとの全消し再ベースライン）の優先順位を決め、個別に起票する。

## 背景

Claude 5 世代向けに Anthropic はシステムプロンプトの 80% を削り、「ルールより判断、手順より結果、前置きより progressive disclosure」へ方針を変えた。dotfiles のハーネスは 2025 の書き方で積み上がっているので、`006-harness-principles` の結論（少数原則）と整合させながら削る対象を決める必要がある。
