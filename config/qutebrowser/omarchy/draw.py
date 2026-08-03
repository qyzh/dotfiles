def apply(c):
    bg        = '#101315'
    fg        = '#cacccc'
    black     = '#101315'
    red       = '#565d60'
    green     = '#9fa5a9'
    yellow    = '#d9dbdc'
    blue      = '#798186'
    magenta   = '#aeaeae'
    cyan      = '#707070'
    white     = '#cbc2be'
    br_black  = '#4b4e55'
    br_red    = '#de6145'
    br_green  = '#343d41'
    br_yellow = '#c9c2b4'
    br_blue   = '#5d6367'
    br_magenta= '#9a9a9a'
    br_cyan   = '#707070'
    br_white  = '#a5aeb4'
    sel_bg    = '#798186'
    sel_fg    = '#101315'
    secondary_background    = '#15181a'
    tertiary_background     = '#1a1d1f'

    # Completion
    c.colors.completion.category.bg = bg
    c.colors.completion.category.fg = blue
    c.colors.completion.category.border.bottom = secondary_background
    c.colors.completion.category.border.top = bg
    c.colors.completion.even.bg = secondary_background
    c.colors.completion.odd.bg = tertiary_background
    c.colors.completion.fg = [fg, fg, fg]
    c.colors.completion.item.selected.bg = sel_bg
    c.colors.completion.item.selected.fg = sel_fg
    c.colors.completion.item.selected.border.bottom = sel_bg
    c.colors.completion.item.selected.border.top = sel_bg
    c.colors.completion.item.selected.match.fg = br_green
    c.colors.completion.match.fg = green
    c.colors.completion.scrollbar.bg = tertiary_background
    c.colors.completion.scrollbar.fg = br_black

    # Context menu
    c.colors.contextmenu.disabled.bg = secondary_background
    c.colors.contextmenu.disabled.fg = br_black
    c.colors.contextmenu.menu.bg = bg
    c.colors.contextmenu.menu.fg = fg
    c.colors.contextmenu.selected.bg = sel_bg
    c.colors.contextmenu.selected.fg = sel_fg

    # Downloads
    c.colors.downloads.bar.bg = bg
    c.colors.downloads.error.bg = red
    c.colors.downloads.error.fg = fg
    c.colors.downloads.start.bg = blue
    c.colors.downloads.start.fg = bg
    c.colors.downloads.stop.bg = green
    c.colors.downloads.stop.fg = bg
    c.colors.downloads.system.bg = 'none'

    # Hints
    c.colors.hints.bg = yellow
    c.colors.hints.fg = bg
    c.colors.hints.match.fg = br_cyan
    c.colors.keyhint.bg = secondary_background
    c.colors.keyhint.fg = fg
    c.colors.keyhint.suffix.fg = yellow

    # Messages
    c.colors.messages.error.bg = red
    c.colors.messages.error.border = red
    c.colors.messages.error.fg = fg
    c.colors.messages.info.bg = bg
    c.colors.messages.info.border = bg
    c.colors.messages.info.fg = fg
    c.colors.messages.warning.bg = yellow
    c.colors.messages.warning.border = yellow
    c.colors.messages.warning.fg = bg

    # Prompts
    c.colors.prompts.bg = secondary_background
    c.colors.prompts.border = '1px solid ' + br_black
    c.colors.prompts.fg = fg
    c.colors.prompts.selected.bg = sel_bg
    c.colors.prompts.selected.fg = sel_fg

    # Statusbar
    c.colors.statusbar.caret.bg = magenta
    c.colors.statusbar.caret.fg = fg
    c.colors.statusbar.caret.selection.bg = magenta
    c.colors.statusbar.caret.selection.fg = fg
    c.colors.statusbar.command.bg = bg
    c.colors.statusbar.command.fg = fg
    c.colors.statusbar.command.private.bg = br_black
    c.colors.statusbar.command.private.fg = fg
    c.colors.statusbar.insert.bg = green
    c.colors.statusbar.insert.fg = bg
    c.colors.statusbar.normal.bg = bg
    c.colors.statusbar.normal.fg = fg
    c.colors.statusbar.passthrough.bg = blue
    c.colors.statusbar.passthrough.fg = fg
    c.colors.statusbar.private.bg = br_black
    c.colors.statusbar.private.fg = fg
    c.colors.statusbar.progress.bg = blue
    c.colors.statusbar.url.error.fg = red
    c.colors.statusbar.url.fg = fg
    c.colors.statusbar.url.hover.fg = cyan
    c.colors.statusbar.url.success.http.fg = fg
    c.colors.statusbar.url.success.https.fg = green
    c.colors.statusbar.url.warn.fg = yellow

    # Tabs
    c.colors.tabs.bar.bg = tertiary_background
    c.colors.tabs.even.bg = secondary_background
    c.colors.tabs.even.fg = fg
    c.colors.tabs.indicator.error = red
    c.colors.tabs.indicator.start = blue
    c.colors.tabs.indicator.stop = green
    c.colors.tabs.indicator.system = 'none'
    c.colors.tabs.odd.bg = tertiary_background
    c.colors.tabs.odd.fg = fg
    c.colors.tabs.pinned.even.bg = bg
    c.colors.tabs.pinned.even.fg = fg
    c.colors.tabs.pinned.odd.bg = bg
    c.colors.tabs.pinned.odd.fg = fg
    c.colors.tabs.pinned.selected.even.bg = black
    c.colors.tabs.pinned.selected.even.fg = fg
    c.colors.tabs.pinned.selected.odd.bg = black
    c.colors.tabs.pinned.selected.odd.fg = fg
    c.colors.tabs.selected.even.bg = black
    c.colors.tabs.selected.even.fg = fg
    c.colors.tabs.selected.odd.bg = black
    c.colors.tabs.selected.odd.fg = fg

    # Webpage
    c.colors.webpage.bg = bg
    c.colors.webpage.preferred_color_scheme = 'dark'
