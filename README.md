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

**キーをこのリポジトリに書かないでください。** マニフェストには `${VAR}` 参照だけを書き、実値は `~/.claude/settings.json` の `env` に置きます（このファイルは gitignore 済みです）。
必要な変数の一覧は `.claude/settings.json.sample` にあります。平文の秘密を書いた場合、同期スクリプトは投入せずに停止します。

### リサーチ用 MCP のキー取得

`ecc:deep-research` などの調査系スキルは exa と firecrawl を使います。どちらも無料枠があり、クレジットカードは不要です。

1. exa: https://exa.ai でサインアップし、API キーを発行する（サインアップ時 $20 ＋ 毎月 $10 のクレジット）
2. firecrawl: https://firecrawl.dev でサインアップし、API キーを発行する（月 1,000 クレジット）
3. `~/.claude/settings.json` の `env` に `EXA_API_KEY` と `FIRECRAWL_API_KEY` を追加する
4. `./setup.sh` を実行する（または `python3 .claude/scripts/sync_mcp.py` を直接実行する）
5. Claude Code を再起動し、`claude mcp list` で接続を確認する

### 注意

- `notion` は OAuth で認証します。定義を入れ直したあとは Claude Code 内で `/mcp` から再認証してください。
- `pencil` はローカルアプリの絶対パスに依存します。インストールされていないマシンでは警告つきで skip されます。
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

---

*このドキュメントは[Claude Code](https://claude.ai/code)によって作成されました。*
