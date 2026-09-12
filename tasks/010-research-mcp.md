---
title: リサーチ用 MCP（exa / firecrawl）を導入する
status: Not started
Project: devops
created_at: 2026-09-12
updated_at: 2026-09-12
---

# リサーチ用 MCP（exa / firecrawl）を導入する

## 概要

ECC の `deep-research` スキルは firecrawl / exa の MCP を前提に作られているが、どちらも未設定。起動しても WebSearch / WebFetch へのフォールバックになり、スキルが想定する検索の網羅性が出ない。リサーチ用 MCP を導入して、調査系スキルを本来の構成で動かせるようにする。API キーの置き場所の方針もあわせて決める。

## 背景

モチベーション・集中力の実証研究を調べる際に ecc:deep-research を起動したところ、MCP が無くフォールバックした。検索スニペット依存になり、効果量やサンプルサイズといった一次情報に到達しにくかった。
