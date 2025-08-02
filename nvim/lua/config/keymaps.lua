-- keymaps.lua - キーボードショートカット設定

-- リーダーキーを設定（多くのカスタムキーマップの起点）
vim.g.mapleader = " "  -- スペースキーをリーダーキーに

local keymap = vim.keymap.set

-- 基本的なキーマップ

-- Normal mode
-- 検索結果のハイライトを消去
keymap("n", "<leader>h", ":nohlsearch<CR>", { desc = "検索ハイライトを消去" })

-- ファイル保存・終了
keymap("n", "<leader>w", ":w<CR>", { desc = "ファイル保存" })
keymap("n", "<leader>q", ":q<CR>", { desc = "終了" })
keymap("n", "<leader>x", ":x<CR>", { desc = "保存して終了" })

-- ウィンドウ分割
keymap("n", "<leader>sh", ":split<CR>", { desc = "水平分割" })
keymap("n", "<leader>sv", ":vsplit<CR>", { desc = "垂直分割" })

-- ウィンドウ間の移動（Ctrl + hjkl）
keymap("n", "<C-h>", "<C-w>h", { desc = "左のウィンドウに移動" })
keymap("n", "<C-j>", "<C-w>j", { desc = "下のウィンドウに移動" })
keymap("n", "<C-k>", "<C-w>k", { desc = "上のウィンドウに移動" })
keymap("n", "<C-l>", "<C-w>l", { desc = "右のウィンドウに移動" })

-- ウィンドウのリサイズ
keymap("n", "<C-Up>", ":resize +2<CR>", { desc = "ウィンドウを上に拡大" })
keymap("n", "<C-Down>", ":resize -2<CR>", { desc = "ウィンドウを下に縮小" })
keymap("n", "<C-Left>", ":vertical resize -2<CR>", { desc = "ウィンドウを左に縮小" })
keymap("n", "<C-Right>", ":vertical resize +2<CR>", { desc = "ウィンドウを右に拡大" })

-- バッファ操作
keymap("n", "<leader>bn", ":bnext<CR>", { desc = "次のバッファ" })
keymap("n", "<leader>bp", ":bprevious<CR>", { desc = "前のバッファ" })
keymap("n", "<leader>bd", ":bdelete<CR>", { desc = "バッファを削除" })

-- Insert mode
-- Escキーの代替（jk で Insert mode を抜ける）
keymap("i", "jk", "<ESC>", { desc = "Insert modeを抜ける" })

-- Visual mode
-- インデントした後も選択を維持
keymap("v", "<", "<gv", { desc = "インデント（選択維持）" })
keymap("v", ">", ">gv", { desc = "インデント（選択維持）" })

-- 選択したテキストを移動
keymap("v", "J", ":m '>+1<CR>gv=gv", { desc = "選択行を下に移動" })
keymap("v", "K", ":m '<-2<CR>gv=gv", { desc = "選択行を上に移動" })

-- 行の移動（Normal mode）
keymap("n", "<A-j>", ":m .+1<CR>==", { desc = "現在行を下に移動" })
keymap("n", "<A-k>", ":m .-2<CR>==", { desc = "現在行を上に移動" })

-- ファイルエクスプローラー（nvim-tree）
keymap("n", "<leader>e", ":NvimTreeToggle<CR>", { desc = "ファイルエクスプローラーの表示切替" })
