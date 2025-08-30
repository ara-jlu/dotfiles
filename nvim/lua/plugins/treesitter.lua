-- plugins/treesitter.lua - 構文ハイライト

return {
  -- 構文ハイライト (Treesitter)
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    config = function()
      require("nvim-treesitter.configs").setup({
        ensure_installed = {
          "javascript", "typescript", "tsx", "lua", "python", 
          "html", "css", "json", "markdown", "markdown_inline",
          "bash", "vim", "yaml", "toml"
        },
        auto_install = true,
        highlight = { 
          enable = true,
        },
      })
    end,
  },
}
