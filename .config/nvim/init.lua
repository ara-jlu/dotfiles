-- init.lua - Neovimのメイン設定ファイル

-- 基本設定を読み込み
require("config.options")
require("config.keymaps")
require("config.lsp")

-- プラグイン設定を読み込み
require("plugins")

-- プラグインでcolorscheme設定後に背景を透過させる
vim.cmd([[
  highlight Normal guibg=none
  highlight NonText guibg=none
  highlight Normal ctermbg=none
  highlight NonText ctermbg=none
  highlight NormalNC guibg=none
  highlight NormalSB guibg=none
]])