#!/bin/bash

# dotfilesセットアップスクリプト
# このスクリプトはnvim、tmux、gitの設定ファイルをシンボリックリンクで配置します
set -e

# スクリプトが配置されているディレクトリ（dotfilesディレクトリ）のパスを取得
DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "dotfilesのセットアップを開始します: $DOTFILES_DIR"

# 既存のファイル・ディレクトリをバックアップする関数
backup_if_exists() {
    local target=$1
    # ファイルまたはディレクトリが存在する場合、またはシンボリックリンクの場合
    if [ -e "$target" ] || [ -L "$target" ]; then
        # タイムスタンプ付きのバックアップ名を生成
        local backup_name="${target}.backup.$(date +%Y%m%d_%H%M%S)"
        echo "既存の $target を $backup_name にバックアップします"
        mv "$target" "$backup_name"
    fi
}

# nvim設定のセットアップ
echo "nvim設定をセットアップしています..."
# 既存のnvim設定をバックアップ
backup_if_exists "$HOME/.config/nvim"
# .configディレクトリが存在しない場合は作成
mkdir -p "$HOME/.config"
# dotfiles/.config/nvimディレクトリへのシンボリックリンクを作成
ln -sf "$DOTFILES_DIR/.config/nvim" "$HOME/.config/nvim"
echo "✓ nvim設定のリンクが完了しました"

# tmux設定のセットアップ
echo "tmux設定をセットアップしています..."
# 既存のtmux設定をバックアップ
backup_if_exists "$HOME/.tmux.conf"
# dotfiles/.config/tmux/tmux.confへのシンボリックリンクを作成
ln -sf "$DOTFILES_DIR/.config/tmux/tmux.conf" "$HOME/.tmux.conf"
echo "✓ tmux設定のリンクが完了しました"

# git設定のセットアップ
echo "git設定をセットアップしています..."
# 既存のgit設定をバックアップ
backup_if_exists "$HOME/.gitconfig"
# dotfiles/.gitconfigへのシンボリックリンクを作成
ln -sf "$DOTFILES_DIR/.gitconfig" "$HOME/.gitconfig"
echo "✓ git設定のリンクが完了しました"

# zsh設定のセットアップ
echo "zsh設定をセットアップしています..."
# 既存のzsh設定をバックアップ
backup_if_exists "$HOME/.zshrc"
# dotfiles/.zshrcへのシンボリックリンクを作成
ln -sf "$DOTFILES_DIR/.zshrc" "$HOME/.zshrc"
echo "✓ zsh設定のリンクが完了しました"

echo ""
echo "dotfilesのセットアップが完了しました！"
echo "既存の設定ファイルはタイムスタンプ付きでバックアップされています。"
echo ""
echo "zshの設定を反映するには、以下を実行してください："
echo "  source ~/.zshrc"