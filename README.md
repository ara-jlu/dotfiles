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
