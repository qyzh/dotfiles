# Omarchy Keybind Integration for Installed Apps

## When to use

Read this when an installed app's README documents Omarchy keybind overrides (usually under "Make <app> the Omarchy file manager" or similar) and you are wiring those overrides into `~/.config/hypr/bindings.lua`.

## Omarchy binding syntax (what the app documents takes precedence)

Two common forms appear in app docs:

### App launch (no cwd dependence)

```lua
hl.unbind("SUPER + SHIFT + F")
o.bind("SUPER + SHIFT + F", "File manager", { launch = "strata" })
```

### Cwd-aware launch (open file manager in the terminal's current directory)

```lua
hl.unbind("SUPER + ALT + SHIFT + F")
o.bind("SUPER + ALT + SHIFT + F", "File manager (cwd)",
  "uwsm-app -- strata \"$(omarchy-cmd-terminal-cwd)\"")
```

The cwd form depends on `uwsm-app` and `omarchy-cmd-terminal-cwd` being present on the system. If either is absent, fall back to a plain launch binding or skip the cwd variant.

## Before wiring any flag into a binding or service

Verify the flag exists:

```bash
<app> --help-all   # GApplication apps expose flag docs here
<app> --help        # shorter list
```

If a flag the app's docs reference (e.g. `--open-cwd`) is not present in `--help-all`, do not wire it. Ask the user or use the documented alternative. A non-existent flag wired into a binding produces a silent no-op or an error at press time.

## Finding the app's documented Omarchy overrides

The overrides usually live in the app's README under a heading like "Make <app> the Omarchy file manager" and may also appear in `docs/packaging.md` or `docs/portal-file-chooser.md`. Fetch the raw README from GitHub when the local copy is stale:

```bash
curl -sL https://raw.githubusercontent.com/<user>/<repo>/main/README.md | grep -A 40 "Make.*Omarchy"
```

Use the syntax in that section verbatim. Do not transpose it into a different binding form.

## Editing a Stow-managed hypr config

On Stow-managed Omarchy installs, `~/.config/hypr` is a symlink into the dotfiles repo (commonly `~/Work/git/dotfiles/config/hypr`). Writing to the live path (`~/.config/hypr/bindings.lua`) updates the repo copy in place (same inode, hardlinked or symlinked target).

Before editing:

```bash
# Confirm whether the live path is the repo copy or a separate file
stat -c '%i %s' ~/.config/hypr/bindings.lua ~/Work/git/dotfiles/config/hypr/bindings.lua
# identical inode = same file; different inode = separate files
```

Back up the file before editing, even though it is already tracked — a timestamped copy in `~/.config/hypr/` costs nothing and gives the user a clean rollback path that does not depend on git):

```bash
cp ~/.config/hypr/bindings.lua ~/.config/hypr/bindings.lua.bak.$(date +%s)
```

After editing, optionally diff against the dotfiles repo copy to confirm the change landed where the user expects:

```bash
diff ~/.config/hypr/bindings.lua ~/Work/git/dotfiles/config/hypr/bindings.lua
```

**Pitfall — assuming the live file and the repo file are independent.** If they are the same inode, an edit to one is an edit to both; a separate backup in the same directory is still useful for rollback but is not a second copy of the content.

**Pitfall — editing the repo copy directly while the live symlink is the active config.** Prefer editing the live path (`~/.config/hypr/`) so the in-use config and the edited file are the same thing; the repo copy follows automatically on a Stow symlink.
