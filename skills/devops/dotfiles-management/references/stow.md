# Stow Reference

## Repo Structure (Stow Convention)

```
repo/
  config/          # ini adalah nama package Stow
    app1/
      file1
      file2
    app2/
      file1
  link.sh          # script manager opsional
```

Saat `stow config`, Stow membuat:
```
~/.config/app1/file1 -> .../repo/config/app1/file1
~/.config/app2/file1 -> .../repo/config/app2/file1
```

## Commands

| Tugas | Perintah (dari root repo) |
|-------|------------------------|
| Link semua | `stow -t "$HOME/.config" -d "$PWD" config` |
| Link satu app (via manager) | `./link.sh` atau `./link.sh config` |
| Unlink semua | `stow -t "$HOME/.config" -d "$PWD" -D config` |
| Adopt file tak-terkelola | `stow -t "$HOME/.config" -d "$PWD" config --adopt` |

## Mendeteksi Repo Stow-Managed

Cari:
- `link.sh` dengan `stow` di dalamnya
- Direktori `config/` berisi subdir app
- `.stowrc` atau `GNUmakefile` dengan target stow

Jika ditemukan, utamakan manager repo daripada symlink manual.

## Conflict Errors

**"cannot stow ... over existing target since neither a link nor a directory"** — file asli ada di target, bukan symlink. Stow tidak akan overwrite tanpa `--adopt`.

**"existing target is not owned by stow"** — direktori target punya file yang tidak diketahui Stow. Either adopt (`--adopt`) atau buat symlink manual hanya untuk app yang dikerjakan.

**"source is an absolute symlink"** — file di dalam package sudah menunjuk ke path absolut lain (misal `/home/user/.local/state/...`). Stow memperingatkan tapi biasanya tetap lanjut; cek apakah target benar setelah linking.
