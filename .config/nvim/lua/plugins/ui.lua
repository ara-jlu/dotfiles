-- plugins/ui.lua - UI・テーマ関連プラグイン

return {
  -- カラースキーム
  {
    'projekt0n/github-nvim-theme',
    name = 'github-theme',
    lazy = false,
    priority = 1000,
    config = function()
      vim.cmd("colorscheme github_dark")
    end,
  },

  -- ファイルアイコン
  {
    "nvim-tree/nvim-web-devicons",
    lazy = false,
    priority = 900,
  },

  -- スタートスクリーン
  {
    "folke/snacks.nvim",
    lazy = false,
    priority = 1000,
    keys = {
      { "<leader>ff", function() Snacks.picker.files({ hidden = true }) end, desc = "ファイル検索" },
      { "<leader>fg", function() Snacks.picker.grep({ hidden = true }) end, desc = "文字列検索" },
      { "<leader>fb", function() Snacks.picker.buffers() end, desc = "バッファ検索" },
      { "<leader>fh", function() Snacks.picker.help() end, desc = "ヘルプ検索" },
      { "<leader>fr", function() Snacks.picker.recent() end, desc = "最近のファイル" },
      { "<leader>fw", function() Snacks.picker.grep_word() end, desc = "カーソル下の単語検索" },
    },
    ---@type snacks.Config
    opts = {
      image = {
        enabled = false, -- WezTermでフリーズするため無効化
      },
      picker = {
        enabled = true,
      },
      dashboard = {
        preset = {
          header = [[
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠶⠞⠛⠛⠛⠋⠉⠉⠉⠛⠷⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡏⠐⢦⡴⠞⠀⠀⠀⠀⠀⠀⢀⡀⠀⣀⡀⠙⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⡴⢦⣾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠋⠉⠀⠀⠈⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⠋⠀⠀⢸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡏⠀⠀⠀⢸⡄⠀⠀⠀⠀⠀⠀⠘⠃⣄⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⢸⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⠶⠶⠶⠶⢤⣬⣷⣀⡀⠀⠈⣧⠀⠀⠀⠀⠀⠀⠀⢾⣽⡇⠀⠀⠀⠀⠀⠀⠀⠀⣠⡿⢧⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠛⠐⠀⠶⢤⣬⣉⣙⠛⠲⠾⣷⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠀⠀⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⡀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠶⠶⣤⣬⣉⡛⠓⣦⡀⠀⠀⠀⠀⠀⢀⣤⠾⠛⠁⠀⠀⠀⠀⢨⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⣠⣤⣄⠀⠀⠀⠀⠉⢁⡄⣿⣭⣛⣛⣛⢳⣶⠏⠁⠀⠀⠀⠀⠀⠀⠀⠈⢿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠘⣇⠀⠀⠀⠀⠀⢰⣏⠀⢹⡇⠀⠀⠀⠀⠀⠃⢸⡦⣤⣉⣹⠟⠁⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⢸⡟⢷⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠉⠛⠋⠀⠀⠀⠀⠀⠀⣿⢸⡿⢿⣭⣿⠀⠀⠀⠀⠀⠀⠀⣠⡶⠶⢦⣤⣴⣇⠈⠇⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣆⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡌⣿⣿⣷⠟⠳⣤⣀⣀⣤⠶⠞⠋⠀⠀⠀⠀⠈⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠓⠶⠦⣤⣤⣀⣀⠀⠀⠀⠀⠀⢸⡇⣿⠉⣀⣴⣾⣿⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠛⠳⠶⣦⣤⣈⠗⢸⣿⣿⠞⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀]],
          keys = {
            { icon = " ", key = "f", desc = "Find File", action = function() Snacks.picker.files({ hidden = true }) end },
            { icon = " ", key = "n", desc = "New File", action = ":ene | startinsert" },
            { icon = " ", key = "r", desc = "Recent Files", action = function() Snacks.picker.recent() end },
            { icon = " ", key = "t", desc = "Find Text", action = function() Snacks.picker.grep({ hidden = true }) end },
            { icon = " ", key = "c", desc = "Config", action = ":e ~/.config/nvim/init.lua" },
            { icon = " ", key = "q", desc = "Quit", action = ":qa" },
          },
        },
        sections = {
          { section = "header" },
          { section = "keys", gap = 1, padding = 1 },
          { icon = " ", title = "Recent Files", section = "recent_files", indent = 2, padding = { 2, 2 } },
          { section = "startup" },
        },
      },
    },
  },

  -- ステータスライン
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    event = "VeryLazy",
    config = function()
      require("lualine").setup({
      })
    end,
  },

  -- インデントガイド
  {
    "lukas-reineke/indent-blankline.nvim",
    event = { "BufReadPost", "BufNewFile" },
    main = "ibl",
    config = function()
      require("ibl").setup({
        indent = { char = "┃" }
      })
    end,
  },
}
