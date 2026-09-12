---
name: install-precompiled-linux-app
description: Install precompiled Linux apps from GitHub releases safely.
version: 1.0.0
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [install, github-release, desktop-integration, verification, desktop-entry, dbus-service]
    related_skills: [dotfiles-management]
---

# Install Precompiled Linux App from GitHub Release

## Trigger

Use when the user asks to install a precompiled Linux binary/app from a GitHub release and wants it done safely: checksum check, optional provenance attestation, per-user binary install, and optional desktop/icon/FileManager1 integration. The upstream README often contains an "AI-assisted installation" prompt — that prompt IS the spec; follow it and consult the README for app-specific answers rather than guessing.

## Always-on rules

- **Checksum is the hard gate.** `sha256sum --check` must pass before extraction. If it fails, stop — do not install a binary with an invalid checksum.
- **Provenance is optional but not soft.** If `gh attestation verify` is attempted, it must also pass; a failed attestation is a stop. If it times out or is interrupted, retry once; if it still cannot complete, report it as unverified rather than failing the install — but never weaken the checksum gate to compensate.
- **Two desktop decisions, asked separately.** The desktop entry + mime association is one ask; the `org.freedesktop.FileManager1` D-Bus service is a separate ask. Do not bundle them.
- **Ask before sudo, ask before changing file-manager association.** Show the package list and the exact association change before using privilege or hijacking the user's default handler.
- **Do not weaken the app's preview sandbox.** Installing the app is out of scope of changing its sandbox policy.
- **Prefer the upstream README over generic patterns for app-specific integration.** Omarchy keybind syntax, portal setup, and service-file `Exec=` format are app-documented; use what the app documents, not a generic guess.

## Procedure

### 1. Confirm the environment

Before changing anything, confirm:
- glibc-based Linux (`ldd --version` / `/proc/version`)
- graphical GTK4/Wayland or X11 session (`XDG_SESSION_TYPE`, `WAYLAND_DISPLAY`/`DISPLAY`, `XDG_CURRENT_DESKTOP`)
- CPU arch: `uname -m`. Map `x86_64` → `*-unknown-linux-gnu`, `aarch64` → `*-unknown-linux-gnu`. If neither, report no prebuilt release and stop.
- Whether `~/.local/bin` is on `PATH` (`echo $PATH` and `ls -d ~/.local/bin`). If missing, say so and ask before adding it — do not silently mutate shell profiles.

Keep this to a short confirmation block. Do not narrate each check.

### 2. Show the runtime deps and ask

Read the app's install docs for the runtime package list (Arch/Omarchy list, Debian equivalents, etc.). Show the exact packages and ask:
- whether to use sudo for the package-manager install
- whether optional extras (SMB via `gvfs-smb`, broader RAW support, etc.) are wanted

Do not run `sudo pacman -S` (or equivalent) before the user confirms.

**Pitfall — doc list is often a superset.** An app's install doc may list packages some distros do not ship under those exact names (e.g. Arch splits gstreamer plugins differently, drops `dcraw` in favour of `libraw`). When a named package is "not found", check whether it has been renamed or split before reporting the install as blocked — but do not silently substitute. The runtime deps that actually matter are the ones the binary spawns or links at preview time (e.g. `bubblewrap` is spawned, not linked — `ldd`/`namcap` will not flag it).

### 3. Detect the release and select the archive

- Use `gh release view --repo <user>/<repo> --json tagName,assets` (or the GitHub API) to get the latest release tag and asset list.
- Select only the archive matching the detected arch: `<name>-<version>-<arch>-unknown-linux-gnu.tar.gz` and its matching `.sha256` file. Download both over HTTPS to `~/Downloads` (or a stated download dir).
- Do not guess the archive name; confirm it is in the release asset list.

### 4. Verify checksum, then optional provenance

```bash
cd ~/Downloads
sha256sum --check <archive>.sha256   # HARD GATE — must say OK
```

Then, only if `gh` is installed and authenticated:

```bash
gh attestation verify <archive> --repo <user>/<repo>
```

If `gh attestation verify` is interrupted or times out (exit 130 / hung), retry once. If it fails verification, stop. If it cannot run at all (no auth, no gh), report that provenance was not verified and continue — checksum is the gate.

### 5. Extract and install the binary

```bash
tar -xzf <archive>.tar.gz
install -Dm755 <extracted>/<app> ~/.local/bin/<app>
```

- Install to `~/.local/bin/<app>` (or the app's stated prefix) without overwriting an unrelated file — `install -Dm755` creates parents and fails if the target is an unrelated non-regular file.
- Confirm with `command -v <app>` that the binary is on PATH.
- If the app has no `--version`, read `SOURCE_COMMIT` (or equivalent) from the extracted archive and report the release tag from `gh release view`. Do not fabricate a version string.
- Briefly launch the app (timeout-bounded) to confirm it starts and paints/loads. Capture the first lines of stdout; do not leave it running.

### 6. Ask about desktop entry + icon + mime association

If yes:
- Install the archive's `io.<owner>.<App>.svg` to `~/.local/share/icons/hicolor/scalable/apps/`.
- Sed the archive's `.desktop` file's `Exec=<app>` → `Exec=$HOME/.local/bin/<app>` (preserve any `%U`/`%f` template), install to `~/.local/share/applications/`.
- Refresh: `update-desktop-database ~/.local/share/applications` and `gtk-update-icon-cache -qtf ~/.local/share/icons/hicolor` (both tolerate "not found" with `2>/dev/null || true`).
- Set the mime default: `xdg-mime default io.<owner>.<App>.desktop inode/directory` and confirm with `xdg-mime query default inode/directory`.

### 7. Ask about FileManager1 (Open file location)

This is separate from step 6. If yes:
- First check that no other per-user service already provides `org.freedesktop.FileManager1`: `ls ~/.local/share/dbus-1/services/org.freedesktop.FileManager1*`. If one exists, stop and report the conflict — two per-user providers for the same name are chosen arbitrarily.
- Sed the archive's `io.<owner>.<App>.FileManager1.service` `Exec=/usr/bin/<app>` → `Exec=$HOME/.local/bin/<app>` (the archive's service almost always ships `Exec=/usr/bin/<app>` or similar; match and replace the exact prefix), install to `~/.local/share/dbus-1/services/`.
- Reload the session bus config: `gdbus call --session --dest org.freedesktop.DBus --object-path /org/freedesktop/DBus --method org.freedesktop.DBus.ReloadConfig` (tolerate failure if no session bus).

### 8. Report and verify

Report: release tag, source commit, installed binary path, checksum + attestation status, and which integrations were installed. Verify the desktop association if one was requested (`xdg-mime query default inode/directory`). Do not claim a desktop association works without checking the query result.

## Style

- Short confirmation blocks, not narratives. State checks, commands, and results in that order.
- When the app documents an integration step (Omarchy keybinds, portal, service format), use the app's documented syntax and verify flags exist before wiring them into bindings or services.
- Back up edited per-user config before mutating it, even under Stow — a timestamped copy in the same dir is cheap insurance.
- When a config path is under a Stow-managed tree (`~/.config/hypr` → dotfiles repo via symlink), writing the live file updates the repo copy; verify with `stat -c %i` on both paths if unsure whether they are the same file. Do not assume.

## Pitfalls

- **Guessing the archive name.** Always confirm the asset is in the release list; release assets can be renamed between versions.
- **Wiring a flag that does not exist.** After installing, check `--help-all` for the flags the app actually exposes before using a flag in a desktop entry, service file, or keybind (e.g. `--open-cwd` may not exist; use what the app documents).
- **Wrong Omarchy binding syntax.** Omarchy keybinds use `{ launch = "<cmd>" }` for app launches and `"uwsm-app -- <cmd> \"$(omarchy-cmd-terminal-cwd)\""` for cwd-aware launches — use the syntax the app's README shows, not a generic `o.bind(..., ..., "cmd")` form.
- **Silent PATH assumption.** `~/.local/bin` is not on every system's PATH by default; check before relying on `command -v`.
- **Assuming the doc package list is exhaustive-and-current.** Distro splits/renames happen; verify what is actually missing rather than reporting the whole list as required.
- **Hardcoding `/usr/bin/<app>` in service/desktop files.** The archive ships a system-path `Exec=`; per-user installs must sed it to the installed absolute path, and the result must be a real absolute path with no whitespace/quotes/backslashes (D-Bus service parsing is not shell quoting).
