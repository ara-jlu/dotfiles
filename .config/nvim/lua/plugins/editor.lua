-- plugins/editor.lua - エディタ・ファイル管理関連プラグイン

return {
  -- プロジェクト全体検索・置換 (Spectre)
  {
    "nvim-pack/nvim-spectre",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      { "<leader>rr", function() require("spectre").open() end, desc = "Search & Replace" },
      { "<leader>rw", function() require("spectre").open_visual({ select_word = true }) end, desc = "Replace Word" },
      { "<leader>rf", function() require("spectre").open_file_search({ select_word = true }) end, desc = "Replace in File" },
    },
    config = function()
      require("spectre").setup({
        live_update = true,      -- tu: ファイル保存時に再検索
        default = {
          find = {
            options = { "hidden", "ignore-case" },  -- th: 隠しファイル, ti: 大文字小文字区別しない
          },
        },
      })
    end,
  },

  -- ファイルエクスプローラー (nvim-tree)
  {
    "nvim-tree/nvim-tree.lua",
    version = "*",
    lazy = false,
    keys = {
      { "<leader>e", "<cmd>NvimTreeToggle<cr>", desc = "Toggle nvim-tree" },
    },
    dependencies = {
      "nvim-tree/nvim-web-devicons",
    },
    config = function()
      require("nvim-tree").setup {
        filters = {
          dotfiles = false,  -- 隠しファイル（.envなど）を表示
          git_ignored = false,  -- .gitignoreされたファイルも表示
        },
        view = {
          width = 30,
        },
        renderer = {
          group_empty = true,
          highlight_git = "name",  -- 文字色でGitステータスを表示
          icons = {
            show = {
              git = false,  -- Gitアイコン（記号）を非表示
            },
          },
        },
        git = {
          enable = true,  -- Git統合を有効化
        },
      }
    end,
  },

  -- ファイル検索（Telescope）
  {
    "nvim-telescope/telescope.nvim", tag = "0.1.8",
    dependencies = { "nvim-lua/plenary.nvim" },
    cmd = { "Telescope" },
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files hidden=true<cr>", desc = "Find Files" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live Grep" },
    },
  },

  -- ターミナル統合 (Toggleterm)
  {
    "akinsho/toggleterm.nvim",
    version = "*",
    keys = {
      { "<leader>tt", "<cmd>ToggleTerm direction=float<cr>", desc = "Float Terminal" },
    },
    config = function()
      require("toggleterm").setup({
        size = function(term)
          if term.direction == "horizontal" then
            return 15
          elseif term.direction == "vertical" then
            return vim.o.columns * 0.4
          end
        end,
        open_mapping = [[<c-\>]],
        hide_numbers = true,
        shade_terminals = false,
        start_in_insert = true,
        insert_mappings = true,
        terminal_mappings = true,
        persist_size = true,
        direction = "float",
        close_on_exit = true,
        shell = vim.o.shell,
        float_opts = {
          border = "curved",
          winblend = 0,
        },
      })
    end,
  },

  -- バッファライン
  {
    "akinsho/bufferline.nvim",
    version = "*",
    dependencies = "nvim-tree/nvim-web-devicons",
    event = "VeryLazy",
    config = function()
      require("bufferline").setup({
        options = {
          diagnostics = "nvim_lsp",
          always_show_bufferline = false,
          offsets = {
            {
              filetype = "NvimTree",
              text = "File Explorer",
              highlight = "Directory",
              text_align = "left",
            },
          },
        },
      })
    end,
  },
}
