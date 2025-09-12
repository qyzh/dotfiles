return {
	-- File explorer utama
	{
		"nvim-neo-tree/neo-tree.nvim",
		branch = "v3.x",
		dependencies = {
			"nvim-lua/plenary.nvim",
			"MunifTanjim/nui.nvim",
			"nvim-tree/nvim-web-devicons",
			"s1n7ax/nvim-window-picker", -- integrasi langsung
		},
		cmd = "Neotree", -- lazy-load hanya saat dipanggil
		keys = {
			{ "<leader>e", "<cmd>Neotree toggle<cr>", desc = "Explorer (Neo-tree)" },
			{ "<leader>o", "<cmd>Neotree focus<cr>", desc = "Focus Neo-tree" },
		},
		config = function()
			require("neo-tree").setup({
				close_if_last_window = true, -- tutup kalau cuma tinggal Neo-tree
				popup_border_style = "rounded",
				enable_git_status = true,
				enable_diagnostics = true,
				default_component_configs = {
					indent = { padding = 0, with_markers = true },
					icon = { folder_closed = "", folder_open = "", default = "" },
					git_status = { symbols = { added = "✚", modified = "", deleted = "✖" } },
				},
				window = {
					width = 30,
					mappings = {
						["<cr>"] = "open_with_window_picker", -- integrasi window picker
						["l"] = "open",
						["h"] = "close_node",
					},
				},
			})
		end,
	},

	-- LSP aware file operations (rename, move, etc.)
	{
		"antosha417/nvim-lsp-file-operations",
		dependencies = { "nvim-neo-tree/neo-tree.nvim" },
		config = function()
			require("lsp-file-operations").setup()
		end,
	},
}
