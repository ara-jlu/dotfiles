---
title: j-devflow の Phase B を既定と `-full` に組み替える 実装計画
tag: [plan]
Project: devops
Task: 017-devflow-light-by-default
created_at: 2026-10-13
updated_at: 2026-10-13
---

# j-devflow の Phase B を既定と `-full` に組み替える 実装計画

**Goal:** j-devflow の Phase B から `-light` を廃止し、「既定（セキュリティ該当のタスクにだけタスク毎レビュー）」と「`-full`（全タスクにタスク毎レビュー）」に組み替え、区分の定義をグローバルな CLAUDE.md の1箇所に置き、joifup 側の dispatcher（joifup-pm）と固有の手掛かりを追随させる。

**Architecture:** 文書だけの変更である。区分の定義・判定の外れの確かめ方・ledger の記録規則は dotfiles の `.claude/CLAUDE.md`（`~/.claude/CLAUDE.md` から symlink され全リポジトリに効く）に置き、j-devflow の SKILL.md はそこを指す。joifup では、固有の手掛かりをリポジトリ直下の `CLAUDE.md` に置き、PM の判断を `joifup-pm/SKILL.md` に書く。根拠は dotfiles の `notes/document/017-devflow-full-flag-design.md` にある。

**Tech Stack:** Markdown（日本語）。検証は `grep`。

## Global Constraints

- 設計書: `<WT>/notes/document/017-devflow-full-flag-design.md`。各タスクの文面はこの設計書の決定に従う。
- dotfiles の自作スキルの本文は日本語。`.claude/rules/skill-language.md` に従う（`default` = 既定、フラグ名・`agentType`・パス・コードは英語のまま、全角の `；` を使わない、英数字と日本語の間に半角スペース）。
- **日本語の本文は桁数で折り返さない**（1文を1行に書く。文の切れ目での改行は可）。
- 一次情報は1箇所: 区分の定義・判定の外れの確かめ方・ledger の記録規則は dotfiles の `.claude/CLAUDE.md` だけに書き、j-devflow の SKILL.md には写さない。根拠の数字は設計書だけに置く。
- j-devflow の SKILL.md には廃止したフラグの名前（`-light`）を書かない。
- joifup の `.claude/skills/joifup-pm/references/incidents.md` は保存用の記録なので、§2.4 の注記1行の追加以外は変えない。
- コミットメッセージは英語の Semantic Commit。各タスク1コミット。末尾に次の2行を付ける:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_01KhmXs1UKWKqieeW86k13aM
  ```

## リポジトリと worktree（orchestrator 向け）

- Task 1・Task 2 は dotfiles の `<WT>`（`/Users/ara/Joifup/dotfiles/.claude/worktrees/feature-017-devflow-light-by-default`）で行う。
- Task 3 は joifup の `<WT_JOIFUP>` で行う。Task 3 を dispatch する前に orchestrator が次を行う:
  1. `cd /Users/ara/Joifup/joifup && git fetch origin && git rev-parse main origin/main`（一致を確認。不一致なら停止して問う）
  2. `cd /Users/ara/Joifup/joifup && git worktree add .claude/worktrees/chore-dotfiles-017-devflow-full-flag -b chore-dotfiles-017-devflow-full-flag origin/main`
  3. `<WT_JOIFUP>` = `/Users/ara/Joifup/joifup/.claude/worktrees/chore-dotfiles-017-devflow-full-flag` を progress ledger のヘッダに記録する。
  4. 書き込みの確かめ: subagent に `<WT_JOIFUP>` で空のコミットを1つ作らせ（`git commit --allow-empty -m "chore: write check"`）、続けて `git reset --hard HEAD~1` で取り消させる。拒否されたら、Task 3 と joifup 側の PR を、joifup のルートで起動する別のセッションに切り出す（設計書「このタスクの進め方」）。
- Task 3 の dispatch は Worktree 固定の契約の `<WT>` を `<WT_JOIFUP>` に読み替えて適用する（assert も同じ形で行う）。
- セキュリティ該当の判定: 3 タスクとも文書だけの変更で、区分（信頼の境界・認証・秘密・公開 API・機微データ）に当たらない。タスク毎レビューは入れない。各タスクの後に `git diff --name-only` でファイル名を確かめる。
- 最終レビューは、dotfiles と joifup の review-package を両方と、この計画を、同じ1回の最終レビューに渡す。

---

### Task 1: dotfiles の CLAUDE.md「レビュー統合」に区分とタスク毎レビューの規則を書く

**Files:**
- Modify: `<WT>/.claude/CLAUDE.md`（「## レビュー統合（superpowers × ECC）」の節。現行の「最終 whole-branch レビュー」の行・「差分が auth / 入力 / …」の行・「タスク毎レビュー」の行）

**Interfaces:**
- Consumes: なし
- Produces: 「セキュリティ該当の区分」という名前の定義（太字の見出し語）。Task 2 の SKILL.md がこの名前で `CLAUDE.md` の「レビュー統合」を指す。

- [ ] **Step 1: 変更前の状態を確かめる（失敗するテスト）**

Run: `grep -c 'セキュリティ該当の区分' .claude/CLAUDE.md; grep -n 'タスク毎レビュー\*\*は superpowers task-reviewer を維持' .claude/CLAUDE.md`
Expected: 1 行目が `0`、2 行目が1件ヒットする。

- [ ] **Step 2: 「最終 whole-branch レビュー」の行の末尾に文を足す**

現行の行:
```
- **最終 whole-branch レビュー**（SDD が全タスク後に自動 dispatch）で、変更言語に対応する `ecc:<lang>-reviewer` を `agentType` 指定で dispatch。review-package の diff を渡し、diff 集中を指示する（コードベースを漁らせない）。
```
新しい行（その下の2つの「例外」「顧客・外部に渡る文書」の子項目はそのまま残す）:
```
- **最終 whole-branch レビュー**（SDD が全タスク後に自動 dispatch）で、変更言語に対応する `ecc:<lang>-reviewer` を `agentType` 指定で dispatch。review-package の diff を渡し、diff 集中を指示する（コードベースを漁らせない）。SDD の最終 code-reviewer（spec 準拠）には、review-package に加えて計画のパスを `[PLAN_OR_REQUIREMENTS]` として渡す（タスク毎レビューを入れないタスクの spec 準拠は、ここでしか見られない）。
```

- [ ] **Step 3: security-reviewer の行を区分を指す形に書き換える**

現行の行:
```
- 差分が auth / 入力 / 秘密 / API / 機微データに触れる場合は `ecc:security-reviewer` も dispatch。
```
新しい行:
```
- 差分が下記の**セキュリティ該当の区分**に触れる場合は `ecc:security-reviewer` も dispatch。
```

- [ ] **Step 4: 「タスク毎レビュー」の行を、区分の定義とタスク毎レビューの規則に置き換える**

現行の行:
```
- **タスク毎レビュー**は superpowers task-reviewer を維持し、上記セキュリティ該当タスクのみ `ecc:security-reviewer` を追加。
```
新しい内容（この位置に、次の2項目と子項目を置く）:
```
- **セキュリティ該当の区分**（タスク毎レビューの判定と、最終レビューの `ecc:security-reviewer` に共通の物差し。定義はここだけに置く）: 次のどれかに触れるもの。
  - 信頼の境界を越えて値を受け取る、または出す経路（利用者の入力・外部のネットワーク・第三者が書ける内容から受け取る、それを HTML・シェル・SQL などに出す）。検証や無害化の有無は問わない。自前のプロセス間の受け渡しや、自リポジトリが管理するファイルを読むだけの経路は含めない。
  - 認証・認可。
  - 秘密（鍵・トークン・資格情報）。
  - 外部に公開する API の契約（ルート・引数・応答の形）。リポジトリの内部だけで呼ぶ関数は含めない。
  - 機微データ（個人情報・顧客データ）の読み書き。
  - リポジトリの `CLAUDE.md` が挙げる手掛かり（ファイルや関数の名前の形）。手掛かりは区分を広げる。上の5項目に当たらなくても該当とする。
- **タスク毎レビュー**は、SDD の orchestrator が計画を読み、各タスクが触るファイルから区分に当たるかを判定して、当たるタスクにだけ superpowers task-reviewer と `ecc:security-reviewer` を入れる。判定結果は progress ledger のヘッダに記録する。全タスクに task-reviewer を入れるのは、依頼者が求めたとき（j-devflow では `-full`）だけである。根拠は dotfiles の `notes/document/017-devflow-full-flag-design.md`。
  - **判定の外れの確かめ:** タスク毎レビューを入れなかったタスクが完了するたびに、`git diff --name-only <base>..<head>` でそのタスクが触ったファイルの名前だけを見て、区分に当たるかを確かめる。当たれば、次のタスクに進む前に、そのタスクに task-reviewer と `ecc:security-reviewer` を dispatch する。diff の本文は orchestrator のコンテキストに入れない。計画のタスクを分けたときは、新しくできたタスクも判定し直す。
  - **ledger の記録:** 確かめが済んでから、`Task N: complete (commits <base7>..<head7>, per-task review: none)` と書く。`review clean` は流用しない（コンパクション後の再開で、レビュー済みと誤読しないため）。
```

- [ ] **Step 5: 書き換えを確かめる**

Run: `grep -c 'セキュリティ該当の区分' .claude/CLAUDE.md; grep -c 'per-task review: none' .claude/CLAUDE.md; grep -c 'PLAN_OR_REQUIREMENTS' .claude/CLAUDE.md; grep -n 'auth / 入力 / 秘密 / API' .claude/CLAUDE.md; grep -n 'task-reviewer を維持' .claude/CLAUDE.md`
Expected: 1 行目が `2`、2・3 行目がそれぞれ `1`、4・5 行目は何も出力しない。
また `sed -n '/## レビュー統合/,/## 記憶/p' .claude/CLAUDE.md` で節全体を通読し、箇条書きの入れ子が崩れていないこと、日本語が桁数で折り返されていないことを目で確かめる。

- [ ] **Step 6: Commit**

```bash
git add .claude/CLAUDE.md
git commit -F - <<'EOF'
docs(claude-md): limit per-task review to security-relevant tasks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KhmXs1UKWKqieeW86k13aM
EOF
```

---

### Task 2: j-devflow の SKILL.md を既定と `-full` に組み替える

**Files:**
- Modify: `<WT>/.claude/skills/j-devflow/SKILL.md`（27・30・32 行、52〜69 行、86〜89 行、99 行、112〜113 行）
- Modify: `<WT>/.claude/rules/skill-language.md`（82 行）

**Interfaces:**
- Consumes: Task 1 の `CLAUDE.md`「レビュー統合」の「セキュリティ該当の区分」「判定の外れの確かめ」「ledger の記録」。SKILL.md はこれらの名前で指すだけで、内容を写さない。
- Produces: なし

- [ ] **Step 1: 変更前の状態を確かめる（失敗するテスト）**

Run: `grep -c -e '-light' -e 'light' .claude/skills/j-devflow/SKILL.md; grep -c -e '-full' .claude/skills/j-devflow/SKILL.md`
Expected: 1 行目が `1` 以上、2 行目が `0`。

- [ ] **Step 2: モード節の冒頭（27・30・32 行）を書き換える**

27 行目を次に置き換える:
```
j-devflow には、異なる 2 つのリスク軸を制御する独立したモードフラグが 2 つある。自由に組み合わせられる: `/j-devflow <id>`、`-auto`、`-full`、`-full -auto`。
```
30 行目（`- **`-light`** は …` の項目）を次に置き換える:
```
- **`-full`** は **Phase B のタスク毎レビューの範囲** を制御する — 既定（セキュリティ該当のタスクにだけタスク毎レビュー） vs 全タスクにタスク毎レビュー。**SDD の「タスク毎に fresh subagent」隔離と、ブランチ全体の最終レビューはどちらでも維持される**。
```
32 行目（「2 つは別のリスクを対象としており…`-light -auto` である。」の段落）を次に置き換える:
```
2 つは別のリスクを対象としており、必ずしも併用する必要はない。`-auto`・`-full` 以外のフラグ（廃止したフラグを含む）を付けて起動されたら、推測で読み替えず、停止して dispatcher に問う。
```

- [ ] **Step 3: 「### Phase B: full（既定） vs `-light`」の節（52〜69 行）を丸ごと置き換える**

52 行目の見出しから 69 行目（「`-auto` と同じ「停止して問う」機構である…」）までを、次で置き換える:
```
### Phase B: 既定 vs `-full`

どちらのモードも `subagent-driven-development` で実装する（タスク毎に fresh subagent — SDD のタスク毎の**隔離**はどちらでも維持される）。違いは**タスク毎レビューを入れる範囲**だけである:

| | 既定 | `-full` |
|---|---|---|
| タスク毎に fresh subagent（SDD の隔離） | あり | あり |
| タスク毎の `task-reviewer` | 該当タスクだけ | 全タスク |
| タスク毎の `ecc:security-reviewer` | 該当タスクだけ | 該当タスクだけ |
| ブランチ全体の最終レビュー | あり | あり |

「該当タスク」の物差し（セキュリティ該当の区分）、判定の外れの確かめ方、progress ledger の記録規則は、`CLAUDE.md` の「レビュー統合」にある。ここには写さない。判定するのは手順 7 の冒頭の orchestrator であり、writing-plans には何も注入しない（計画を読む側で判定する）。

**既定でタスク毎レビューを絞る理由:** 重要な正しさの網は、SDD の「タスク毎に fresh subagent」の隔離と、ブランチ全体の最終レビューである。タスク毎レビューの層は、実測でほとんど欠陥を拾っていない。ただし実測の n は小さいので directional として扱い、全タスクに戻す `-full` を残す。根拠の数字は dotfiles の `notes/document/017-devflow-full-flag-design.md` にある。**ブランチ全体の最終レビューは絶対に弱めない**: これは常に fresh subagent であり、実装した subagent や orchestrator の会話は絶対に受け取らない（自己レビューのバイアス）。

**`-full` を付けるかを決めるのは誰か:** 起動時に dispatcher（PM セッションか人間）が決める（`-auto` の起動時の選択と同じ形）。タスク毎レビューを入れるタスクは、j-devflow の orchestrator が計画から決める。`joifup-pm/SKILL.md` を参照。

**Phase B の停止条件（両モード共通） — 停止して dispatcher に問う:**
- 設計に無かったスキーマ変更・データ移行・削除・セキュリティや認証のポリシーの変更・公開 API の契約変更が必要だと判明した — `-auto` の条件と同じ、不可逆で影響範囲が大きい区分である。

`-auto` と同じ「停止して問う」機構である: 停止し、dispatcher に問いを提示し、回答を得て再開する。
```

- [ ] **Step 4: 手順 7 の2つの分岐（86・87 行）を置き換え、88 行の文言を合わせる**

86 行（`- **full（既定）:** …`）と 87 行（`- **`-light`:** …`）の2行を、次の2行で置き換える:
```
   - **既定:** `superpowers:subagent-driven-development` — タスク毎に fresh subagent、英語の atomic commit。最初のタスクを dispatch する前に、計画の各タスクがセキュリティ該当の区分（`CLAUDE.md` の「レビュー統合」）に当たるかを判定し、結果を progress ledger のヘッダに `<WT>` と並べて記録する。該当タスクにだけ `task-reviewer` と `agentType: ecc:security-reviewer` を入れる。該当しないタスクは、完了ごとに `CLAUDE.md` の規定どおりファイル名で判定の外れを確かめ、確かめが済んでから ledger に記録する。orchestration と fix のループは Driver が持ち続ける — subagent になるのはタスク毎の単位だけである。
   - **`-full`:** 既定と同じだが、全タスクに `task-reviewer` を入れる。`ecc:security-reviewer` は該当タスクにだけ入れる。
```
88 行の中で、次の2箇所を置き換える（それ以外は1文字も変えない）:
- `（subagent の dispatch すべて — implementer・fix・reviewer。full も `-light` も同様）` → `（subagent の dispatch すべて — implementer・fix・reviewer。既定も `-full` も同様）`
- `この固定の契約は full と `-light` に**同一に**適用される。` → `この固定の契約は既定と `-full` に**同一に**適用される。`

- [ ] **Step 5: 手順 8（89 行）を置き換える**

89 行を次に置き換える:
```
8. ブランチ全体のレビュー: fresh に dispatch し、受け手ごとに渡すものを分ける — **SDD の最終 code-reviewer（spec 準拠）**には review-package と永続化された計画のパス（`[PLAN_OR_REQUIREMENTS]`）を、**`ecc:<lang>-reviewer`**（変更された言語に応じて）と、diff がセキュリティ該当の区分に触れるなら **`ecc:security-reviewer`** には review-package だけを渡す。どの受け手にも、実装した subagent と orchestrator の会話コンテキストは絶対に渡さない。既定でも `-full` でも同じである。Critical/Important はブロッキングであり → clean になるまで fix ループを回す。修正後の再レビューも同じ fresh な dispatch を通し、修正を行ったセッションによる自己チェックにはしない。**既定では、該当しないタスクの spec 準拠を見るのはこのレビューだけである。**
```

- [ ] **Step 6: ガードとよくある失敗（99・112・113 行）を書き換える**

99 行の中の `— `-auto` も `-light` もこの基準を下げてはならない。` を `— `-auto` も既定の Phase B もこの基準を下げてはならない。` に置き換える。

112 行（`- **旧 inline の `-light` を復活させる** — …`）を削除し、その位置に次の2行を置く:
```
- **ブランチ全体の最終レビューに計画を要件として渡さない** — 既定では、該当しないタスクの spec 準拠を見るのは最終レビューだけである。計画のファイルが diff に入っているだけでは、照らし合わせる要件として扱われない。
- **該当の判定を writing-plans への注入で済ませる** — 計画に判定を書かせるのはラップである。判定は計画を読む側（Phase B の orchestrator）で行う。
```

113 行の中の `— `-light` ではこれが唯一のレビューなので、` を `— 既定では、該当しないタスクにとってこれが唯一のレビューなので、` に置き換える。

- [ ] **Step 7: skill-language.md の識別子の例（82 行）を書き換える**

82 行の中の `（`attended` / `-auto` / `-light` / `full` / `Phase A` / `GATE 1`）` を `（`attended` / `-auto` / `-full` / `Phase A` / `GATE 1`）` に置き換える。

- [ ] **Step 8: 書き換えを確かめる**

Run: `grep -rn -e 'light' .claude/skills/j-devflow/ .claude/rules/skill-language.md | grep -iv highlight; grep -c -e '-full' .claude/skills/j-devflow/SKILL.md; grep -c 'セキュリティ該当の区分' .claude/skills/j-devflow/SKILL.md; grep -c 'PLAN_OR_REQUIREMENTS' .claude/skills/j-devflow/SKILL.md; grep -c 'per-task review: none' .claude/skills/j-devflow/SKILL.md`
Expected: 1 行目は何も出力しない。2〜4 行目はそれぞれ `1` 以上。5 行目は `0`（記録規則は CLAUDE.md にだけ置き、写さない）。
また `sed -n '/## モード/,/## 手順書/p' .claude/skills/j-devflow/SKILL.md` と `sed -n '/^7\./,/^9\./p' .claude/skills/j-devflow/SKILL.md` を通読し、表が崩れていないこと、日本語が桁数で折り返されていないこと、`full（既定）` のような旧い言い方が残っていないことを確かめる。

- [ ] **Step 9: Commit**

```bash
git add .claude/skills/j-devflow/SKILL.md .claude/rules/skill-language.md
git commit -F - <<'EOF'
feat(j-devflow): replace -light with default and -full review modes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KhmXs1UKWKqieeW86k13aM
EOF
```

---

### Task 3: joifup の CLAUDE.md と joifup-pm を追随させる

**Worktree root はこのタスクだけ `<WT_JOIFUP>`**（`/Users/ara/Joifup/joifup/.claude/worktrees/chore-dotfiles-017-devflow-full-flag`）。

**Files:**
- Modify: `<WT_JOIFUP>/CLAUDE.md`（「## PM / orchestration session の規律」の見出しの直前に節を1つ足す）
- Modify: `<WT_JOIFUP>/.claude/skills/joifup-pm/SKILL.md`（46 行）
- Modify: `<WT_JOIFUP>/.claude/skills/joifup-pm/references/incidents.md`（81 行の見出し「### 2.4 `-light` の可否」の直後に注記1行）

**Interfaces:**
- Consumes: dotfiles の `CLAUDE.md`「レビュー統合」の「セキュリティ該当の区分」（名前で指すだけ）。
- Produces: なし

- [ ] **Step 1: 変更前の状態を確かめる（失敗するテスト）**

Run: `grep -c 'タスク毎レビューの該当の手掛かり' CLAUDE.md; grep -n -e '-light' .claude/skills/joifup-pm/SKILL.md`
Expected: 1 行目が `0`、2 行目は 46 行目が1件ヒットする。

- [ ] **Step 2: joifup の CLAUDE.md に手掛かりの節を足す**

`## PM / orchestration session の規律` の見出しの直前（その前の節の本文の後、空行を1つ挟んで）に、次を挿入する:
```
## タスク毎レビューの該当の手掛かり（j-devflow）

j-devflow の既定の Phase B は、セキュリティ該当の区分（dotfiles の `CLAUDE.md`「レビュー統合」）に当たるタスクにだけタスク毎レビューを入れる。この repo では、次の名前の形に触れるタスクも該当とする（区分の5項目に当たらなくても該当。手掛かりは区分を広げる）:

- `sanitize*`
- `*-href`
- 入力の検証系
- daemon の公開ルート
- 書き込み経路の fail-closed ガード

出どころは `.claude/skills/joifup-pm/references/incidents.md` §2.4（2026-08-15 の 208 の失敗例）。

```

- [ ] **Step 3: joifup-pm/SKILL.md の 46 行を書き換える**

現行の行:
```
**`-light` の可否**: 起票時点で「サニタイザ / 入力検証 / auth / 秘密 / 公開 API / 機微データに触る」と分かるなら**不可**。設計判断が残らず原因が特定済みなら light。**迷ったら full。**
```
新しい行:
```
**`-full` の可否**: 既定で足りる。タスク毎レビューを入れるタスクは j-devflow が計画から判定する（区分は dotfiles の `CLAUDE.md`「レビュー統合」、この repo の手掛かりは `CLAUDE.md`）。`-full` は、原因が特定できていないデバッグや UX の設計面が残るなど、全タスクを念のため見たいときだけ付ける。**迷ったら既定。**
```

- [ ] **Step 4: incidents.md の §2.4 の見出しの直後に注記を足す**

`### 2.4 `-light` の可否` の行の直後に、空行・注記・空行を挿入する（見出し・索引・既存の本文は変えない）:
```

> **2026-10-13 注記:** `-light` は dotfiles の `tasks/017` で廃止した（Phase B は既定と `-full` になった）。現行の判断は `SKILL.md` の「`-full` の可否」にある。以下は当時の記録として残す。
```

- [ ] **Step 5: 書き換えを確かめる**

Run: `grep -n -e '-light' .claude/skills/joifup-pm/SKILL.md CLAUDE.md; grep -c 'タスク毎レビューの該当の手掛かり' CLAUDE.md; grep -c '2026-10-13 注記' .claude/skills/joifup-pm/references/incidents.md; git diff --stat`
Expected: 1 行目は何も出力しない。2・3 行目はそれぞれ `1`。`git diff --stat` は3ファイルで、incidents.md は `+2`（空行と注記）だけ。

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md .claude/skills/joifup-pm/SKILL.md .claude/skills/joifup-pm/references/incidents.md
git commit -F - <<'EOF'
docs(joifup-pm): follow j-devflow default and -full review modes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01KhmXs1UKWKqieeW86k13aM
EOF
```

---

## 最終確認（orchestrator・最終レビューの後）

- `cd <WT> && grep -rn -e '-light' .claude/ --include='*.md' | grep -v '^.claude/worktrees/'` が何も出力しない。
- `cd <WT_JOIFUP> && grep -n -e '-light' CLAUDE.md .claude/skills/joifup-pm/SKILL.md` が何も出力しない。
- PR: dotfiles は `j-finish`（Task 017 を In review に）、joifup は `j-pr`。両方の PR 本文で互いを参照し、「2本ともマージし、両方のローカルの main を更新してから、次の j-devflow を起動する」と書く。UI が無いので UAT は省き、`## テスト` に上の grep の結果を書く。
