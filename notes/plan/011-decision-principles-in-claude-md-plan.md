---
title: 判断の原則を CLAUDE.md に載せる 実装計画
tag: [plan]
Project: devops
Task: 011-decision-principles-in-claude-md
created_at: 2026-09-22
updated_at: 2026-09-22
---

# 判断の原則を CLAUDE.md に載せる 実装計画

**Goal:** `.claude/CLAUDE.md` の先頭に「判断の原則」の節（見出し + 1 文）を追加する。

**Architecture:** 変更は markdown ファイル 1 つに 4 行（見出し・空行・本文・区切りの空行）を挿入するだけである。何を載せて何を載せないかの線引きは設計書 `notes/document/011-decision-principles-in-claude-md-design.md` で確定しており、この計画はその文言を一字も変えずに置く。

**Tech Stack:** markdown、git。

## Global Constraints

- 追加する文言は設計書の「載せる文」と完全に一致させる。言い換え・補足・ポインタの追加はしない。
- 日本語の本文は桁数で折り返さない（`CLAUDE.md` § 言語）。本文は 1 行に収める。
- 変更するファイルは `.claude/CLAUDE.md` だけ。他の節には触れない。
- dotfiles は public リポジトリなので、事業名・個人の経緯・個人の notes へのパスは書かない。
- コミットメッセージは英語（Semantic Commit）。

---

### Task 1: CLAUDE.md に「判断の原則」の節を追加する

**Files:**
- Modify: `.claude/CLAUDE.md:1-3`（`# Development Rules` と `## ハーネス構成` の間に挿入）

**Interfaces:**
- Consumes: なし。
- Produces: `.claude/CLAUDE.md` の `## 判断の原則` 節。以後の全セッションが読む。

- [ ] **Step 1: 挿入位置を確認する**

Run: `sed -n 1,3p .claude/CLAUDE.md`
Expected:

```
# Development Rules

## ハーネス構成
```

1 行目が `# Development Rules`、2 行目が空行、3 行目が `## ハーネス構成` であることを確認する。違っていれば STOP して報告する（設計書が前提にしている構造が変わっている）。

- [ ] **Step 2: 節を挿入する**

`.claude/CLAUDE.md` の 2 行目（空行）の直後に、次の 4 行（見出し・空行・本文・空行）を挿入する。本文は改行せず 1 行に置く。

```markdown
## 判断の原則

回復不能なリスクは徹底的に避け、回復可能なリスクは速く取る。自分の作業にも、ユーザーの判断への問い返しにも当てる。

```

挿入後の先頭 7 行は次のようになる。

```markdown
# Development Rules

## 判断の原則

回復不能なリスクは徹底的に避け、回復可能なリスクは速く取る。自分の作業にも、ユーザーの判断への問い返しにも当てる。

## ハーネス構成
```

- [ ] **Step 3: diff が挿入だけであることを確認する**

Run: `git diff --stat .claude/CLAUDE.md`
Expected: `1 file changed, 4 insertions(+)` — 削除が 0 であること。

Run: `git diff .claude/CLAUDE.md`
Expected: `+` の行が `## 判断の原則`、空行、本文、空行の 4 行だけで、`-` の行が無いこと。

- [ ] **Step 4: 本文が 1 行で、設計書の文言と一致することを確認する**

Run: `grep -c '回復不能なリスクは徹底的に避け、回復可能なリスクは速く取る。自分の作業にも、ユーザーの判断への問い返しにも当てる。' .claude/CLAUDE.md`
Expected: `1`

この grep が 1 を返せば、本文が 1 行に収まっており（桁数で折り返されていない）、かつ設計書の文言と一致している。

- [ ] **Step 5: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs(claude): put the decision principle at the top of CLAUDE.md"
```
