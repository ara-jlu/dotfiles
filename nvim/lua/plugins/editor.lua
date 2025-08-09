-- plugins/editor.lua - エディタ・ファイル管理関連プラグイン

return {
  -- ファイルエクスプローラー (nvim-tree)
  {
    "nvim-tree/nvim-tree.lua",
    dependencies = {
      "nvim-tree/nvim-web-devicons",
    },
    keys = {
      { "<leader>e", "<cmd>NvimTreeToggle<cr>", desc = "Toggle nvim-tree" },
      { "<leader>fe", "<cmd>NvimTreeFocus<cr>", desc = "Focus nvim-tree" },
    },
    config = function()
      -- アイコンを事前に定義
      vim.fn.sign_define("NvimTreeDiagnosticError", { text = " ", texthl = "DiagnosticError" })
      vim.fn.sign_define("NvimTreeDiagnosticWarn", { text = " ", texthl = "DiagnosticWarn" })
      vim.fn.sign_define("NvimTreeDiagnosticInfo", { text = " ", texthl = "DiagnosticInfo" })
      vim.fn.sign_define("NvimTreeDiagnosticHint", { text = "󰌵", texthl = "DiagnosticHint" })

      require("nvim-tree").setup({
        disable_netrw = true,
        hijack_netrw = true,
        hijack_cursor = false,
        update_cwd = true,
        
        -- 診断設定を修正
        diagnostics = {
          enable = true,
          show_on_dirs = true,
          debounce_delay = 50,
          icons = {
            hint = "󰌵",
            info = " ",
            warning = " ",
            error = " ",
          },
        },
        
        update_focused_file = {
          enable = true,
          update_root = false,
          ignore_list = {},
        },
        
        git = {
          enable = true,
          ignore = true,
          show_on_dirs = true,
          show_on_open_dirs = true,
          timeout = 400,
        },
        
        view = {
          centralize_selection = false,
          cursorline = true,
          debounce_delay = 15,
          width = 30,
          side = "left",
          preserve_window_proportions = false,
          number = false,
          relativenumber = false,
          signcolumn = "yes",
        },
        
        renderer = {
          add_trailing = false,
          group_empty = false,
          highlight_git = false,
          full_name = false,
          highlight_opened_files = "none",
          root_folder_label = ":~:s?$?/..?",
          indent_width = 2,
          indent_markers = {
            enable = false,
            inline_arrows = true,
            icons = {
              corner = "└",
              edge = "│",
              item = "│",
              bottom = "─",
              none = " ",
            },
          },
          icons = {
            webdev_colors = true,
            git_placement = "before",
            modified_placement = "after",
            padding = " ",
            symlink_arrow = " ➛ ",
            show = {
              file = true,
              folder = true,
              folder_arrow = true,
              git = true,
              modified = true,
            },
            glyphs = {
              default = "",
              symlink = "",
              bookmark = "󰆤",
              modified = "●",
              folder = {
                arrow_closed = "",
                arrow_open = "",
                default = "",
                open = "",
                empty = "",
                empty_open = "",
                symlink = "",
                symlink_open = "",
              },
              git = {
                unstaged = "✗",
                staged = "✓",
                unmerged = "",
                renamed = "➜",
                untracked = "★",
                deleted = "",
                ignored = "◌",
              },
            },
          },
          special_files = { "Cargo.toml", "Makefile", "README.md", "readme.md" },
          symlink_destination = true,
        },
        
        filters = {
          dotfiles = false,
          git_clean = false,
          no_buffer = false,
          custom = {},
          exclude = {},
        },
        
        actions = {
          use_system_clipboard = true,
          change_dir = {
            enable = true,
            global = false,
            restrict_above_cwd = false,
          },
          expand_all = {
            max_folder_discovery = 300,
            exclude = {},
          },
          file_popup = {
            open_win_config = {
              col = 1,
              row = 1,
              relative = "cursor",
              border = "shadow",
              style = "minimal",
            },
          },
          open_file = {
            quit_on_open = false,
            resize_window = true,
            window_picker = {
              enable = true,
              picker = "default",
              chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
              exclude = {
                filetype = { "notify", "lazy", "qf", "diff", "fugitive", "fugitiveblame" },
                buftype = { "nofile", "terminal", "help" },
              },
            },
          },
        },
      })
    end,
  },

  -- ファイル検索（Telescope）
  {
    "nvim-telescope/telescope.nvim",
    tag = "0.1.4",
    dependencies = { 
      "nvim-lua/plenary.nvim",
      {
        "nvim-telescope/telescope-fzf-native.nvim",
        build = "make",
      },
    },
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find Files" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live Grep" },
      { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Buffers" },
      { "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "Help Tags" },
      { "<leader>fr", "<cmd>Telescope oldfiles<cr>", desc = "Recent Files" },
      { "<leader>fw", "<cmd>Telescope grep_string<cr>", desc = "Word Under Cursor" },
    },
    config = function()
      local telescope = require("telescope")
      telescope.setup({
        defaults = {
          file_ignore_patterns = { "node_modules", ".git", "lazy-lock.json" },
          prompt_prefix = "🔍 ",
          selection_caret = "➤ ",
          layout_config = {
            horizontal = { prompt_position = "top" },
          },
          sorting_strategy = "ascending",
        },
        pickers = {
          find_files = { theme = "dropdown" },
          live_grep = { theme = "dropdown" },
          buffers = { theme = "dropdown" },
        },
      })
      telescope.load_extension("fzf")
    end,
  },

  -- ターミナル統合 (Toggleterm)
  {
    "akinsho/toggleterm.nvim",
    version = "*",
    keys = {
      { "<leader>tf", "<cmd>ToggleTerm direction=float<cr>", desc = "Float Terminal" },
      { "<leader>th", "<cmd>ToggleTerm direction=horizontal<cr>", desc = "Horizontal Terminal" },
      { "<leader>tv", "<cmd>ToggleTerm direction=vertical size=80<cr>", desc = "Vertical Terminal" },
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