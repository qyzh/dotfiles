-- nvim-origami: folding quality-of-life (LSP/Treesitter folds, fold-text
-- decorations, h/l/^/$ fold keymaps, auto-fold comments/imports, pause on search).
-- Replaces nvim-ufo — DO NOT install nvim-ufo alongside this (incompatible).
-- Requires Neovim 0.11+.
-- stylua: ignore
return {
  {
    "chrisgrieser/nvim-origami",
    event = "VeryLazy",
    -- recommended: disable vim's own auto-folding so origami controls it
    init = function()
      vim.opt.foldlevel = 99
      vim.opt.foldlevelstart = 99
    end,
    opts = {
      useLspFoldsWithTreesitterFallback = {
        enabled = true,
        foldmethodIfNeitherIsAvailable = "indent",
      },
      pauseFoldsOnSearch = true,
      foldtext = {
        enabled = true,
        padding = { character = " ", width = 3, hlgroup = nil },
        lineCount = { template = "%d lines", hlgroup = "Comment" },
        diagnosticsCount = true, -- uses vim.diagnostic signs icons/hlgroups
        gitsignsCount = true,   -- needs gitsigns.nvim or mini.diff (gitsigns is installed)
        disableOnFt = { "snacks_picker_input" },
      },
      autoFold = {
        enabled = true,
        kinds = { "comment", "imports" }, -- needs an LSP that provides folding ranges
      },
      foldKeymaps = {
        setup = true,             -- overload h / l / ^ / $ for fold open/close
        closeOnlyOnFirstColumn = false,
        scrollLeftOnCaret = false,
      },
    },
  },
}
