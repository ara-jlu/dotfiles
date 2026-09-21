# dotfiles

個人用のdotfiles設定ファイル管理リポジトリです。

## 含まれる設定

- **nvim**: Neovim エディタの設定
- **tmux**: ターミナルマルチプレクサの設定
- **git**: Git のalias設定
- **zsh**: Zsh シェルの設定

## ディレクトリ構成

```
dotfiles/
├── .config/
│   ├── nvim/          # Neovim設定
│   └── tmux/          # tmux設定
│       └── tmux.conf
├── .gitconfig         # Git設定（alias含む）
├── .zshrc             # Zsh設定
├── setup.sh           # セットアップスクリプト
└── README.md
```

## セットアップ手順

### 1. リポジトリをクローン

```bash
git clone git@github.com:daiki-jlu/dotfiles.git
cd dotfiles
```

### 2. セットアップスクリプトを実行

```bash
./setup.sh
```

このスクリプトは以下の処理を行います：

- 既存の設定ファイルを自動的にバックアップ（タイムスタンプ付き）
- `~/.config/nvim` → `./.config/nvim` へのシンボリックリンクを作成
- `~/.tmux.conf` → `./.config/tmux/tmux.conf` へのシンボリックリンクを作成
- `~/.gitconfig` → `./.gitconfig` へのシンボリックリンクを作成
- `~/.zshrc` → `./.zshrc` へのシンボリックリンクを作成

セットアップ後、zshの設定を反映するには：
```bash
source ~/.zshrc
```

## 手動セットアップ（スクリプトを使わない場合）

```bash
# nvim設定
ln -sf $(pwd)/.config/nvim ~/.config/nvim

# tmux設定
ln -sf $(pwd)/.config/tmux/tmux.conf ~/.tmux.conf

# git設定
ln -sf $(pwd)/.gitconfig ~/.gitconfig

# zsh設定
ln -sf $(pwd)/.zshrc ~/.zshrc
```

## MCP サーバー

Claude Code の MCP サーバー定義は `.claude/mcp-servers.json` が正典です。`setup.sh` が `claude mcp add-json --scope user` で `~/.claude.json` に冪等に反映します（2 回目以降は「変更はありません」と表示されます）。

### API キーの置き場所

**キーをこのリポジトリに書かないでください。** マニフェストには `${VAR}` 参照だけを書き、実値は `~/.claude/settings.json` の `env` に置きます。平文の秘密を書いた場合、同期スクリプトは投入せずに停止します。

`~/.claude/settings.json` の実体は、このリポジトリの `.claude/settings.json` です（`setup.sh` がシンボリックリンクを張ります）。
**このファイルは gitignore 済みなので、clone した直後には存在しません。** 先に雛形からコピーしてください。コピーしないまま `setup.sh` を実行すると、リンク先の無いシンボリックリンクができあがります。

```bash
cp .claude/settings.json.sample .claude/settings.json
# `env` の <YOUR_...> を実値に書き換える
```

必要な変数の一覧は `.claude/settings.json.sample` の `env` にあります。

### リサーチ用 MCP のキー取得

`ecc:deep-research` などの調査系スキルは exa と firecrawl を使います。どちらも無料枠があり、クレジットカードは不要です。

1. exa: https://exa.ai でサインアップし、API キーを発行する（サインアップ時 $20 ＋ 毎月 $10 のクレジット）
2. firecrawl: https://firecrawl.dev でサインアップし、API キーを発行する（月 1,000 クレジット）
3. `~/.claude/settings.json` の `env` に `EXA_API_KEY` と `FIRECRAWL_API_KEY` を追加する
4. `./setup.sh` を実行する（または `python3 .claude/scripts/sync_mcp.py` を直接実行する）
5. Claude Code を再起動し、下記の手順でキーが効いているかを確認する

### 効いているかの確認

**`claude mcp list` の `✔ Connected` は確認になりません。** exa も firecrawl も、API キーが無いまま起動しても MCP サーバーとしては立ち上がるので `✔ Connected` と表示されます。キーの有無を区別できるのは、Claude Code の `/mcp` で各サーバーを開いたときに出る診断です。

- `Missing environment variables` と出ていれば、キーが解決できていません。`~/.claude/settings.json` の `env` を見直し、Claude Code を再起動してください（`settings.json` は起動時に読まれます）。
- 何も出ていなければ、キーは解決できています。

`python3 .claude/scripts/sync_mcp.py` も、参照されている `${VAR}` が `settings.json` の `env` にもシェル環境にも無ければ、投入する前に `⚠ <VAR> が未設定です` と警告します。

### 注意

- **`n8n-mcp` は現在このマシンで API アクセスができない状態です。** マニフェスト化にあたって平文のキーを `${N8N_API_KEY}` 参照に変えましたが、この変数がまだ `settings.json` の `env` に入っていません。実値を `~/.claude/settings.json` の `env` に移してください。**あわせて、以前のキーは n8n 側でローテートしてください** — 設計時の調査で会話ログに平文のまま現れたため、露出したものとして扱う必要があります。
- `notion` は OAuth で認証します。定義を入れ直したあとは Claude Code 内で `/mcp` から再認証してください。
- ローカルアプリの絶対パスに依存するサーバーは、その実行ファイルが無ければ警告つきで skip されます。
- マニフェストから消したサーバーは `~/.claude.json` からは消えません（削除の同期は行いません）。不要になったサーバーは `claude mcp remove <name> --scope user` で手動で消してください。

## Git Alias

以下のaliasが設定されています：

| Alias | コマンド | 説明 |
|-------|---------|------|
| `cob` | `checkout -b` | 新しいブランチを作成してチェックアウト |
| `ps` | `push` | リモートにプッシュ |
| `b` | `branch` | ブランチ一覧表示 |
| `bd` | `branch -D` | ブランチを強制削除 |
| `st` | `status` | ステータス表示 |
| `co` | `checkout` | ブランチをチェックアウト |
| `cm` | `commit` | コミット |
| `pl` | `pull` | リモートからプル |
| `lg` | `log --oneline --graph --decorate` | グラフ形式のログ表示 |

**注意**: `git`コマンド自体を`g`にするエイリアスは`.zshrc`に設定されています。

## バックアップについて

既存の設定ファイルがある場合、`設定ファイル名.backup.YYYYMMDD_HHMMSS` という形式でバックアップされます。

## 注意事項

- このセットアップはmacOS環境を想定しています
- 設定を変更した場合は、このリポジトリ内のファイルを編集してください
- `.claude/statusline-command.sh` は `jq` を使います。入っていないマシンでは statusLine が `Unknown | Context: --` になるので `brew install jq` を実行してください（他の設定には影響しません）

---

*このドキュメントは[Claude Code](https://claude.ai/code)によって作成されました。*
