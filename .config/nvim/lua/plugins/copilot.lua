return {
	"github/copilot.vim",
	cmd = "Copilot",
	build = ":Copilot auth",
	eevent = "InsertEnter",
	config = function()
		require("copilot").setup({
			panel = {
				enabled = true,
				auto_refresh = true,
				keymap = {
					jump_prev = "[[",
					jump_next = "]]",
					accept = "<CR>",
					refresh = "gr",
					open = "<M-CR>",
				},
				layout = {
					position = "right", -- top, bottom, left, right
					ratio = 0.4,
				},
				suggestion = {
					enabled = true,
					auto_trigger = false,
					hide_during_completion = true,
					debounce = 75,
					trigger_on_accept = true,
					keymap = {
						accept = "<M-l>",
						accept_word = false,
						accept_line = false,
						next = "<M-]>",
						prev = "<M-[>",
						dismiss = "<C-]>",
					},
				},
				copilot_node_command = "node", -- Node.js version must be > 16.x
				working_file_types = { -- default is not defined so all file types are supported
					"python",
					"lua",
					"javascript",
					"typescript",
					"typescriptreact",
					"html",
					"css",
					"markdown",
				},
				copilot_model = "",
			},
		})
	end,
}
