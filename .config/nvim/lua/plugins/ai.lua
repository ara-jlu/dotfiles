-- plugins/ai.lua - AI補完関連プラグイン

return {
  -- Codeium AI補完
  {
    "Exafunction/codeium.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    event = "InsertEnter",
    cmd = { "Codeium" },
    config = function()
      require("codeium").setup({
        enable_cmp_source = false,
        virtual_text = {
          enabled = true,
          key_bindings = {
            accept = "<Tab>",
            next = "<C-n>",
            prev = "<C-p>",
            clear = "<C-]>",
          },
        },
      })
      -- ゴースト文字をグレーに設定
      vim.api.nvim_set_hl(0, "CodeiumSuggestion", { fg = "#808080", italic = true })
    end,
  },
}
