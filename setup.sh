#!/bin/bash

# dotfilesセットアップスクリプト
# このスクリプトはnvimとtmuxの設定ファイルをシンボリックリンクで配置します
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
# dotfiles/nvimディレクトリへのシンボリックリンクを作成
ln -sf "$DOTFILES_DIR/nvim" "$HOME/.config/nvim"
echo "✓ nvim設定のリンクが完了しました"

# tmux設定のセットアップ
echo "tmux設定をセットアップしています..."
# 既存のtmux設定をバックアップ
backup_if_exists "$HOME/.tmux.conf"
# dotfiles/.tmux.confへのシンボリックリンクを作成
ln -sf "$DOTFILES_DIR/.tmux.conf" "$HOME/.tmux.conf"
echo "✓ tmux設定のリンクが完了しました"

echo ""
echo "dotfilesのセットアップが完了しました！"
echo "既存の設定ファイルはタイムスタンプ付きでバックアップされています。"