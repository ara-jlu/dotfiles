-- plugins/init.lua - プラグイン管理の統合設定

-- lazy.nvimの自動インストール
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- lazy.nvimを初期化（モジュール化されたプラグイン設定を読み込み）
require("lazy").setup({
  { import = "plugins.ui" },        -- UI・テーマ関連
  { import = "plugins.editor" },    -- エディタ・ファイル管理
  { import = "plugins.lsp" },       -- LSP・自動補完
  { import = "plugins.git" },       -- Git統合
  { import = "plugins.treesitter" }, -- 構文ハイライト・編集支援
}, {
  defaults = {
    lazy = false,
    version = false,
  },
  install = { colorscheme = { "github_dark" } },
  checker = { enabled = true },
  performance = {
    cache = {
      enabled = true,
    },
    rtp = {
      disabled_plugins = {
        "gzip",
        "matchit",
        "matchparen", 
        "netrwPlugin",
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
})