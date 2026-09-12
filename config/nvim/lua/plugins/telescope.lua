--
-- Telescope plugin configuration
-- Keymaps:
--   <leader>ff  = Find Files (current directory)
--   <leader>fg  = Live Grep (ripgrep)
--   <leader>fb  = Buffers
--   <leader>fh  = Help Tags
--   <leader>fp  = Find Plugin File (LazyVim root)
--
return {
  "nvim-telescope/telescope.nvim",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-telescope/telescope-fzf-native.nvim",
    build = "make",
  },
  cmd = "Telescope",
  keys = {
    { "<leader>ff", function() require("telescope.builtin").find_files() end, desc = "Find Files" },
    { "<leader>fg", function() require("telescope.builtin").live_grep() end, desc = "Live Grep" },
    { "<leader>fb", function() require("telescope.builtin").buffers() end, desc = "Buffers" },
    { "<leader>fh", function() require("telescope.builtin").help_tags() end, desc = "Help Tags" },
    {
      "<leader>fp",
      function() require("telescope.builtin").find_files({ cwd = require("lazy.core.config").options.root }) end,
      desc = "Find Plugin File",
    },
  },
  opts = {
    defaults = {
      layout_strategy = "horizontal",
      layout_config = {
        prompt_position = "top",
        preview_width = 0.5,
      },
      sorting_strategy = "ascending",
      winblend = 0,
      border = true,
      borderchars = { "─", "│", "─", "│", "╭", "╮", "╯", "╰" },
    },
    pickers = {
      find_files = {
        hidden = true,
        no_ignore = false,
        no_ignore_parent = false,
      },
      live_grep = {
        grep_open_files = true,
        show_line = true,
      },
    },
  },
}
