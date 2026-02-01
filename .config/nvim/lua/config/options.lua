-- options.lua - Neovimの基本設定

local opt = vim.opt

-- シェル設定
vim.o.shell = "/bin/zsh"

-- エンコーディング設定
opt.encoding = "utf-8"
opt.fileencoding = "utf-8"

-- インデント設定
opt.shiftwidth = 4      -- インデント幅
opt.tabstop = 4         -- タブ文字の幅
opt.expandtab = true    -- タブをスペースに変換
opt.autoindent = true   -- 自動インデント
opt.smartindent = true  -- スマートインデント

-- 検索設定
opt.hlsearch = true     -- 検索結果をハイライト
opt.incsearch = true    -- インクリメンタル検索
opt.ignorecase = true   -- 大文字小文字を区別しない
opt.smartcase = true    -- 大文字が含まれる場合は区別する

-- 表示設定
opt.number = true       -- 行番号を表示
opt.relativenumber = false -- 相対行番号を表示しない
opt.cursorline = true   -- カーソル行をハイライト
opt.wrap = true         -- 行の折り返しを有効
opt.signcolumn = "yes"  -- サインカラムを常に表示

-- クリップボード設定
opt.clipboard = "unnamed" -- システムクリップボードを使用

-- バックアップ・スワップファイル設定
opt.backup = false      -- バックアップファイル無効
opt.writebackup = false -- 書き込み時バックアップ無効
opt.swapfile = false    -- スワップファイル無効

-- 外部変更の自動検知（Claude Code等で編集された場合に自動反映）
opt.autoread = true
vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold" }, {
  command = "checktime",
})

-- その他の設定
opt.updatetime = 250    -- 更新間隔を短く
opt.timeoutlen = 300    -- キーマップのタイムアウト
opt.scrolloff = 8       -- スクロール時の余白
opt.sidescrolloff = 8   -- 横スクロール時の余白

-- ページャー・メッセージ設定
opt.more = false        -- ページャー無効化
opt.cmdheight = 2       -- コマンドライン高さ
opt.shortmess:append("c") -- 一部メッセージを短縮

-- カラー設定
opt.termguicolors = true -- 24bit色を有効
vim.cmd("syntax on")     -- シンタックスハイライト有効
