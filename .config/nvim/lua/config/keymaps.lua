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
keymap("n", "<leader>e", "<cmd>NvimTreeToggle<CR>", { desc = "nvim-tree切り替え" })
keymap("n", "<leader>fe", "<cmd>NvimTreeFocus<CR>", { desc = "nvim-treeフォーカス" })

-- Telescope（ファイル検索）
keymap("n", "<leader>ff", "<cmd>Telescope find_files<CR>", { desc = "ファイル検索" })
keymap("n", "<leader>fg", "<cmd>Telescope live_grep<CR>", { desc = "文字列検索" })
keymap("n", "<leader>fb", "<cmd>Telescope buffers<CR>", { desc = "バッファ検索" })
keymap("n", "<leader>fh", "<cmd>Telescope help_tags<CR>", { desc = "ヘルプ検索" })
keymap("n", "<leader>fr", "<cmd>Telescope oldfiles<CR>", { desc = "最近のファイル" })
keymap("n", "<leader>fw", "<cmd>Telescope grep_string<CR>", { desc = "カーソル下の単語検索" })

-- ターミナル（Toggleterm）
keymap("n", "<leader>tf", "<cmd>ToggleTerm direction=float<CR>", { desc = "フローティングターミナル" })
keymap("n", "<leader>th", "<cmd>ToggleTerm direction=horizontal<CR>", { desc = "水平ターミナル" })
keymap("n", "<leader>tv", "<cmd>ToggleTerm direction=vertical size=80<CR>", { desc = "垂直ターミナル" })
keymap("n", "<C-\\>", "<cmd>ToggleTerm<CR>", { desc = "ターミナル切り替え" })
keymap("t", "jk", [[<C-\><C-n>]], { desc = "ターミナルでNormal mode" })

-- LSP診断（エラー・警告）
keymap("n", "[d", vim.diagnostic.goto_prev, { desc = "前の診断" })
keymap("n", "]d", vim.diagnostic.goto_next, { desc = "次の診断" })
keymap("n", "<leader>d", vim.diagnostic.open_float, { desc = "診断情報を表示" })
keymap("n", "<leader>dl", vim.diagnostic.setloclist, { desc = "診断リストを表示" })

-- LSP機能（LSPアタッチ時に自動設定）
-- gd: 定義ジャンプ
-- K: ホバー情報
-- gr: 参照一覧
-- <space>rn: リネーム
-- <space>ca: コードアクション

-- Git操作（メイン）
keymap("n", "<leader>gg", "<cmd>Neogit<CR>", { desc = "Neogit (Git UI)" })
keymap("n", "<leader>gd", "<cmd>DiffviewOpen<CR>", { desc = "Git差分表示" })
keymap("n", "<leader>gh", "<cmd>DiffviewFileHistory<CR>", { desc = "ファイル履歴" })
keymap("n", "<leader>gc", "<cmd>Neogit commit<CR>", { desc = "Neogit Commit" })
keymap("n", "<leader>gp", "<cmd>Neogit push<CR>", { desc = "Neogit Push" })
keymap("n", "<leader>gl", "<cmd>Neogit pull<CR>", { desc = "Neogit Pull" })

-- Git（Gitsigns - ハンク操作）
keymap("n", "]c", function()
  if vim.wo.diff then return "]c" end
  vim.schedule(function() require("gitsigns").next_hunk() end)
  return "<Ignore>"
end, { expr = true, desc = "次のGitハンク" })

keymap("n", "[c", function()
  if vim.wo.diff then return "[c" end
  vim.schedule(function() require("gitsigns").prev_hunk() end)
  return "<Ignore>"
end, { expr = true, desc = "前のGitハンク" })

-- Git（バックアップ・ターミナル）
keymap("n", "<leader>glz", "<cmd>LazyGit<CR>", { desc = "LazyGit" })
keymap("n", "<leader>gt", "<cmd>terminal git status<CR>", { desc = "Git Status (Terminal)" })
keymap("n", "<leader>gf", "<cmd>Git<CR>", { desc = "Fugitive (Git Status)" })
