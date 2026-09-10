---
name: omarchy-icon-font
description: Add branded glyphs to the Omarchy icon font.
version: 0.1.0
author: Omacom (omacom), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, fonts, icons]
    related_skills: []
---

# Omarchy Icon Font Skill

Read this before adding a branded glyph to `default/fonts/omarchy/omarchy.ttf`.

The Omarchy icon font is a small private-use font carrying the marks Nerd
Fonts does not have: the Omarchy logo and the agent and app brand marks. The
menu draws one by naming the font on an entry:

```jsonc
"setup.default.agent.grok": {"icon":"","iconFont":"omarchy","label":"Grok", ...}
```

Without `iconFont`, an entry's `icon` is drawn in the menu font, so reach for
this font only when a Nerd Font glyph would misrepresent the thing. A generic
robot for four different AI apps is the case that justifies a real mark; a
folder or a microphone is not.

`default/fonts/omarchy/README.md` lists every glyph with the URL its artwork
came from. Keep that list accurate — it is the only record of provenance.

## When to Use

- Adding a new branded glyph to the Omarchy icon font.
- Updating the font README provenance list.
- Verifying a newly added glyph renders correctly.

**Don't use for:** adding generic Nerd Font glyphs (use Nerd Font directly), or multi-color app favicons.

## Prerequisites

- `omarchy dev font` command available.
- Source SVG: monochrome, single `<path>`.

## Quick Reference

```bash
omarchy dev font list
omarchy dev font add ollama https://simpleicons.org/icons/ollama.svg
```

## Procedure

1. **Pick a source.** The source must be a monochrome SVG with a single `<path>` — the menu recolors the glyph with the active theme's foreground and selection colors. Brand icon sets such as https://simpleicons.org publish exactly that shape. App favicons usually do not (multi-color, container tile, several paths). Prefer the official mark when published as flat monochrome art; fall back to an icon set's redraw otherwise.
2. **Avoid two-tone marks.** Every path becomes solid foreground, so a logo whose meaning depends on lighter and darker halves turns into an unreadable blob. Pick a source whose silhouette alone reads.
3. **Add the glyph.** `omarchy dev font add <name> <svg-url>` fetches the SVG, scales it into the same 64..960 box the existing marks use, appends it at the next free private-use codepoint, and adds a line to the font README. It prints the codepoint and the glyph itself.
4. **After adding:**
   - Point the menu entry at the new codepoint with `"iconFont":"omarchy"`.
   - Bump the charset range asserted in `test/shell.d/menu-test.sh`; that test pins the font's coverage and fails until it matches.
   - Check the README line the command added, and give it a proper display name with `--label` if the glyph name is not the brand's name.

## Font Ownership

The font is package-owned: `omarchy-settings` installs it to
`/usr/share/fonts/omarchy/omarchy.ttf`, so a new glyph reaches the desktop
through a settings release, not through `omarchy update`. Between the merge and
that release, a pulled checkout renders the new entry with no icon.

## Verifying

Render the whole font and look at it, which catches inverted contours and
filled counters that a glyph list cannot show:

```bash
python3 -c "open('/tmp/row.txt','w').write(' '.join(chr(c) for c in range(0xE900, 0xE910)))"
magick -background white -fill black -font default/fonts/omarchy/omarchy.ttf \
  -pointsize 110 label:@/tmp/row.txt /tmp/font-row.png
```

Then confirm it in the running menu per the visual verification skill. Avoid leaving two fonts with the `omarchy` family registered: Qt can use an old copy in `~/.local/share/fonts` even when `fc-match omarchy` reports the packaged font. For a preview, either replace the packaged file in the disposable VM or temporarily exclude it with a `<rejectfont>` rule in `~/.config/fontconfig/conf.d/` before loading the candidate.

Refresh the font cache and restart the shell afterwards — Qt reads the font database at startup, so `omarchy menu refresh` alone will not pick up a changed font. Remove temporary fonts and rules after verification.

## Pitfalls

- Multi-path or multi-color SVGs — they render as an unreadable solid blob.
- Two-tone logos — meaning is lost when every path becomes solid foreground.
- Forgetting to bump the charset range in `test/shell.d/menu-test.sh`.
- Leaving a temporary font or fontconfig rule in place after verification.
