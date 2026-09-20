---
title: リサーチ用 MCP（exa / firecrawl）の導入と MCP 定義の dotfiles 化
tag: [document]
Project: devops
Task: 010-research-mcp
created_at: 2026-09-20
updated_at: 2026-09-20
---

# リサーチ用 MCP（exa / firecrawl）の導入と MCP 定義の dotfiles 化

## 背景と問題

ECC の `deep-research` スキルは firecrawl / exa の MCP を前提に作られている。どちらも未設定なので、起動しても WebSearch / WebFetch へのフォールバックになり、検索スニペット依存になる。実際にモチベーション・集中力の実証研究を調べた際、効果量やサンプルサイズといった一次情報に到達できなかった。

調査の過程で、より根の深い問題が分かった。**MCP 定義は `~/.claude.json`（Claude Code の状態ファイル、git 管理外）にしか存在せず、dotfiles には一切の記録が無い。** 現在 8 つのサーバー（playwright / context7 / notion / google-analytics / pencil / gsc / chrome-devtools / n8n-mcp）がすべて手作業で入っている。

手作業であることの実害は既に出ている。

- `google-analytics` は `env` で `${GA4_PROPERTY_ID}` を参照しているが、`~/.claude/settings.json` の `env` にその変数の定義が無い。参照先が欠けたまま放置されている。
- `n8n-mcp` は `N8N_API_KEY` を平文で直書きしている。`context7` や `google-analytics` が `${VAR}` 参照なのに対して、一貫していない。

つまり「リサーチ用 MCP を入れる」という要求は、**MCP 定義を dotfiles の再現対象にする**という、より一般的な問題の特殊ケースである。今回は両方を解く。

## 決定事項

### 接続方式: stdio + npx

exa / firecrawl はいずれもリモート HTTP エンドポイントを提供している（exa は `https://mcp.exa.ai/mcp` に `x-api-key` ヘッダ、firecrawl は `https://mcp.firecrawl.dev/v2/mcp` に `Authorization: Bearer`）。それでも **stdio + npx を採る**。

理由は、このリポジトリに既に確立された `${VAR}` 参照パターンにそのまま乗れることである。`context7` は `args` で、`google-analytics` は `env` で `${VAR}` を使っており、展開が動く実績がある。ヘッダ値での `${VAR}` 展開には実績が無く、検証コストが増える。npx の起動時間差は調査系スキルの実行時間に対して無視できる。

採用する定義は次のとおり。

- exa: `npx -y exa-mcp-server`、`env` に `EXA_API_KEY: ${EXA_API_KEY}`
- firecrawl: `npx -y firecrawl-mcp`、`env` に `FIRECRAWL_API_KEY: ${FIRECRAWL_API_KEY}`

### API キーの置き場所: `~/.claude/settings.json` の `env`

既存の `CONTEXT7_API_KEY` と同じ扱いにする。`settings.json` の実体は dotfiles では gitignore 済みなので、秘密がリポジトリに入らない。`settings.json.sample` にプレースホルダを置いて、必要な変数が一覧で分かるようにする。

これがタスクの「API キーの置き場所の方針もあわせて決める」への回答である。新しい機構は導入しない。

### 適用範囲: 既存 8 つも含めて全 10 サーバー

仕組みだけ汎用に作って exa / firecrawl の 2 つにしか使わない、という形にはしない。上に書いたとおり既存 8 つの手作業が実際に劣化を生んでいるので、同じ仕組みに載せる。

## 構成

### 新規ファイル

`.claude/mcp-servers.json` が正典である。`{"mcpServers": {...}}` 形式で 10 サーバーを宣言する。**不変条件: 平文の秘密を書かない。** 秘密は必ず `${VAR}` 参照にする。

`.claude/scripts/sync_mcp.py` がマニフェストを `claude mcp` に冪等反映する。既存の `unwrap.py` と同じく、純粋関数と薄い副作用層に分ける。

`.claude/scripts/test_sync_mcp.py` が純粋関数を検証する。既存の `test_unwrap.py` と同じ Python `unittest` 形式。

### 変更するファイル

`setup.sh` に同期の呼び出しを追加する。`.claude/settings.json.sample` に不足している env プレースホルダ（`EXA_API_KEY` / `FIRECRAWL_API_KEY` / `GA4_PROPERTY_ID` / `N8N_API_KEY`）を追加する。

### データフロー

```
.claude/mcp-servers.json  ──読む──▶ sync_mcp.py ──▶ claude mcp add-json --scope user ──▶ ~/.claude.json
                                        │
                                        ├─ 秘密混入検査（平文なら即停止）
                                        ├─ 差分計算（同一なら何もしない）
                                        └─ 必要 env の充足検査（欠けていれば警告）
```

### 純粋関数（テスト対象）

- `scan_plaintext_secrets(manifest)` — キー名が `KEY|TOKEN|SECRET|PASSWORD` に該当するのに値が `${...}` でないものを検出する。
- `required_env_vars(manifest)` — 定義中の全 `${VAR}` を抽出する。
- `diff_servers(manifest, current)` — 追加 / 更新 / 一致 に分類する。冪等性の本体である。

副作用（`claude mcp add-json` と `claude mcp remove` の実行、現在の定義の読み取り）は薄い層に隔離する。テストは純粋関数だけを対象にする。

## 個別事情

`pencil` はローカルアプリの絶対パス（`/Applications/Pencil.app/...`）に依存する。実行ファイルが無ければ skip し、警告だけ出す。失敗にはしない。

`notion` は OAuth で認証する HTTP サーバーである。定義を投入し直すと再認証が必要になる。この事実を手順に明記する。

`n8n-mcp` の平文 API キーは `${N8N_API_KEY}` 参照に移行する。実値は `settings.json` に移す。なおこのキーは設計時の調査で会話ログに露出したので、移行と同時にローテーションすることを推奨する。

`claude` CLI が PATH に無い環境では、同期を警告つきでスキップする。MCP の同期に失敗しただけで nvim や tmux の設定まで巻き込んで `setup.sh` 全体を止めるべきではない。

## エラー処理の強度

| 事象 | 扱い |
|---|---|
| マニフェストに平文の秘密 | 即停止（exit 非 0）。リポジトリへの秘密混入を構造的に防ぐ |
| マニフェストが不正な JSON | 即停止 |
| `claude` CLI が無い | 警告してスキップ（exit 0） |
| `${VAR}` が未定義 | 警告（どの変数がどのサーバーで必要かを表示）。exit 0 |
| `pencil` の実行ファイルが無い | 警告してそのサーバーのみ skip |
| `claude mcp add-json` が失敗 | そのサーバーを失敗として記録し、残りは続行。最後にまとめて報告し exit 非 0 |

秘密混入だけを即停止にしているのは、それが唯一の**取り返しがつかない**事故だからである。一度 push した秘密は履歴に残る。env の欠落やアプリの不在は、後から直せば済む。

## テスト

`test_sync_mcp.py` で純粋関数を対象に検証する。

- 平文検出の陽性（`"N8N_API_KEY": "eyJ..."` を検出する）と陰性（`"N8N_API_KEY": "${N8N_API_KEY}"` を検出しない）
- `${VAR}` 抽出（`args` の中と `env` の中の両方から拾う）
- 差分分類（新規追加 / 値が変わった / 完全一致 の 3 通り。冪等性はここで担保する）
- 不正な JSON を渡したときに停止すること

`claude` CLI の実行はテストしない。副作用層を薄く保つことで担保する。

## 受け入れ基準

1. `python3 .claude/scripts/test_sync_mcp.py` が green。
2. `./setup.sh` を 2 回連続実行して、2 回目に「変更なし」と報告される（冪等性）。
3. 同期後に `claude mcp list` で exa / firecrawl が接続済みと表示される。
4. `ecc:deep-research` を起動して、WebSearch フォールバックではなく `web_search_exa` / `firecrawl_search` が実際に呼ばれる。
5. リポジトリ内の全ファイルに平文の API キーが存在しない。

1・2・5 は機械が検証できる。3 と 4 は API キーの取得が前提なので、キー投入後に人間が確認する（UAT に相当する）。

## スコープ外

**削除の同期**は入れない。マニフェストから消したサーバーを `~/.claude.json` からも消す機能である。誤って全消しする事故のリスクに対して、得られるものが小さい。追加と更新だけを行う。

**API キーの自動取得**も入れない。exa も firecrawl もサインアップが必要で（exa はサインアップ $20 + 毎月 $10 クレジット、firecrawl は月 1,000 クレジット、どちらもカード不要）、これは人間の作業である。手順を docs に書くに留める。
