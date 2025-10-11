-- config/lsp.lua - LSP設定

-- 補完設定
vim.opt.completeopt = {"menu", "menuone", "noselect"}

-- LSPサーバー設定（vim.lsp.config使用）
local lsp_servers = {
  -- Lua Language Server
  lua_ls = {
    cmd = {'lua-language-server'},
    filetypes = {'lua'},
    root_markers = {'.luarc.json', '.luarc.jsonc', '.git'},
    settings = {
      Lua = {
        runtime = {version = 'LuaJIT'},
        diagnostics = {globals = {'vim'}},
        workspace = {
          checkThirdParty = false,
          library = {vim.env.VIMRUNTIME}
        },
        completion = {callSnippet = "Both"},
      },
    },
    on_attach = function(client, bufnr)
      vim.lsp.completion.enable(true, client.id, bufnr, {autotrigger = true})
    end,
  },
  
  -- TypeScript/JavaScript
  ts_ls = {
    cmd = {'typescript-language-server', '--stdio'},
    filetypes = {'typescript', 'typescriptreact', 'javascript', 'javascriptreact'},
    root_markers = {'package.json', 'tsconfig.json', 'jsconfig.json', '.git'},
    on_attach = function(client, bufnr)
      vim.lsp.completion.enable(true, client.id, bufnr, {autotrigger = true})
    end,
  },
  
  -- Terraform
  terraformls = {
    cmd = {'terraform-ls', 'serve'},
    filetypes = {'terraform', 'tf', 'hcl'},
    root_markers = {'*.tf', '.terraform', '.git'},
    on_attach = function(client, bufnr)
      vim.lsp.completion.enable(true, client.id, bufnr, {autotrigger = true})
    end,
  },
  
  -- Python（必要時にコメントアウト解除）
  --[[
  pyright = {
    cmd = {'pyright-langserver', '--stdio'},
    filetypes = {'python'},
    root_markers = {'pyproject.toml', 'setup.py', 'requirements.txt', '.git'},
    on_attach = function(client, bufnr)
      vim.lsp.completion.enable(true, client.id, bufnr, {autotrigger = true})
    end,
  },
  --]]
}

-- LSP設定を適用・有効化
for name, config in pairs(lsp_servers) do
  vim.lsp.config[name] = config
end
vim.lsp.enable(vim.tbl_keys(lsp_servers))

-- =============================================================================
-- Neovim 0.11+ デフォルトキーマップ（自動設定される）
-- =============================================================================
-- K      : ホバー情報（vim.lsp.buf.hover）
-- grr    : 参照一覧（vim.lsp.buf.references）  
-- gri    : 実装へジャンプ（vim.lsp.buf.implementation）
-- grn    : リネーム（vim.lsp.buf.rename）
-- gra    : コードアクション（vim.lsp.buf.code_action）
-- gO     : ドキュメントシンボル（vim.lsp.buf.document_symbol）
-- [d     : 前の診断（vim.diagnostic.goto_prev）
-- ]d     : 次の診断（vim.diagnostic.goto_next）

-- VS Code風補完キー操作
vim.keymap.set('i', '<Tab>', function()
  return vim.fn.pumvisible() == 1 and '<C-n>' or '<Tab>'
end, {expr = true})

vim.keymap.set('i', '<S-Tab>', function()
  return vim.fn.pumvisible() == 1 and '<C-p>' or '<S-Tab>'
end, {expr = true})

vim.keymap.set('i', '<CR>', function()
  return vim.fn.pumvisible() == 1 and '<C-y>' or '<CR>'
end, {expr = true})

vim.keymap.set('i', '<Esc>', function()
  return vim.fn.pumvisible() == 1 and '<C-e><Esc>' or '<Esc>'
end, {expr = true})
