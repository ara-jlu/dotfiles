---
ID: TASK-838
title: j-devflow で設計書を書いた後に fresh なレビューを入れる
status: In progress
Project: devops
created_at: 2026-10-02
updated_at: 2026-10-08
---

# j-devflow で設計書を書いた後に fresh なレビューを入れる

## 概要

`j-devflow` の Phase A では、設計書（spec）を書いた後のレビューが、書いた本人による自己レビューだけである。設計の対話を持たない fresh な subagent に設計書を読ませるレビューを、計画（writing-plans）に進む前に入れるかどうか、入れるならどこに・何を渡して行うかを決める。

## 背景

2026-10-02、fde の `tasks/097` で、自己レビューを通した設計書に、題材の芯に関わる穴（受け取り方の前提から、添付で届く注文書を扱えなくなる）が残り、依頼者が読んで見つけた。
