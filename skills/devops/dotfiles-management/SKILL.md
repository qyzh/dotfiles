---
name: dotfiles-management
description: "Manage dotfiles with symlinks or Stow."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [dotfiles, symlinks, stow, config-management]
---

# Dotfiles Management

## Overview

Store config files in a git repo and symlink them into `~/.config/` (or other standard locations). Two common setups: manual symlinks, or GNU Stow managing the links.

## Before You Start

1. **Inspect the repo first.** Look for `link.sh`, `stow` calls, or a `config/` package directory. If the repo is Stow-managed, use its manager — not manual `ln -s`.
2. **Verify the target directory exists** before creating any symlink. Run `ls <target>` or `test -d <target>` — a symlink to a non-existent path is broken and useless.

## Manual Symlink Approach

```bash
# From $HOME, create symlink with ABSOLUTE target path
ln -s /path/to/repo/config/hypr ~/.config/hypr

# Verify it works
cat ~/.config/hypr/hyprland.lua | head -n 5
```

**Always use absolute paths for the symlink target.** Relative paths break when the working directory changes — the symlink stores the path literally, not relative to `~`.

## Stow-Managed Repo Approach

If the repo has a `link.sh` like:
```bash
stow -t "$HOME/.config" -d "$PWD" config
```

Then the package is `config` (the directory under the repo root), and apps live under `config/<app>/`. To link one app:

```bash
# From the repo root
./link.sh          # links all of config/
./link.sh config   # explicit
```

**Do NOT run `stow hypr`** — Stow looks for a package directory named `hypr/` at the repo root, not `config/hypr/`. The correct invocation is `stow config` (or `./link.sh`).

### Stow Conflicts

If `stow` aborts dengan "existing target is not owned by stow" atau "cannot stow ... over existing target":

- **Opsi A — adopt:** `stow -t "$HOME/.config" -d "$PWD" config --adopt` — memindahkan file yang ada ke package dan membuat symlink.
- **Opsi B — manual:** buat symlink hanya untuk app yang dibutuhkan, biarkan sisanya.

## Pitfalls

- **Path target salah.** Symlink dibuat ke `repo/dotfiles/config/hypr` padahal path aslinya `repo/config/hypr`. Selalu `ls` target sebelum membuat symlink.
- **CWD drift.** `ln -s Work/git/dotfiles/config/hypr .config/hypr` dari `~` berhasil; perintah yang sama dari root repo membuat symlink di dalam repo. Cek `pwd` sebelum linking.
- **Kebingungan nama package Stow.** `stow hypr` mencari `hypr/` di root repo. Jika repo pakai wrapper `config/`, stow `config`, bukan nama app.
- **Tanpa verifikasi.** Membuat symlink belum selesai — verifikasi dengan membaca file melaluinya. Symlink ke tempat salah tampak identik dengan yang benar di `ls -la`.
- **Symlink absolut warning.** Stow memperingatkan "source is an absolute symlink" saat file di dalam package sudah menunjuk ke path absolut lain. Biasanya tidak fatal; cek target setelah linking.

## Style

- Singkat dan langsung. Tanpa kapitalisasi berlebihan untuk penekanan.
- Nyatakan perintah, alasan, dan verifikasi — dalam urutan itu. Jangan narasi jejak debugging kecuali diminta.
