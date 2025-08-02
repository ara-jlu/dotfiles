# dotfiles

個人用のdotfiles設定ファイル管理リポジトリです。

## 含まれる設定

- **nvim**: Neovim エディタの設定
- **tmux**: ターミナルマルチプレクサの設定

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
- `~/.config/nvim` → `./nvim` へのシンボリックリンクを作成
- `~/.tmux.conf` → `./.tmux.conf` へのシンボリックリンクを作成

## 手動セットアップ（スクリプトを使わない場合）

```bash
# nvim設定
ln -sf $(pwd)/nvim ~/.config/nvim

# tmux設定  
ln -sf $(pwd)/.tmux.conf ~/.tmux.conf
```

## バックアップについて

既存の設定ファイルがある場合、`設定ファイル名.backup.YYYYMMDD_HHMMSS` という形式でバックアップされます。

## 注意事項

- このセットアップはmacOS環境を想定しています
- 設定を変更した場合は、このリポジトリ内のファイルを編集してください

---

*このドキュメントは[Claude Code](https://claude.ai/code)によって作成されました。*
