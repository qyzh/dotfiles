-- cord.nvim: Discord Rich Presence for Neovim (Rust-powered, no Rust toolchain needed).
-- Auto-fetches its server binary via curl on first load; ensure curl is installed.
-- Requires an active Discord client running to show presence.
-- See https://github.com/vyfor/cord.nvim/wiki/Configuration for full options.
return {
  {
    "vyfor/cord.nvim",
    event = "VeryLazy",
    opts = {
      -- Match Omarchy's Catppuccin look (options: default, atom, catppuccin,
      -- minecraft, void, classic). Each has dark/light/accent flavors.
      display = {
        theme = "catppuccin",
      },
    },
  },
}
