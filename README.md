# dotfiles — Omarchy Linux

Config pribadi dikelola **GNU Stow**. Paket di `config/<app>/`, symlink ke `~/.config/<app>`.

## Apps ditrack
`hypr waybar qutebrowser mako nvim kitty foot alacritty fish cava btop imv fastfetch nwg-dock-hyprland`

## Setup (baru)
```bash
git clone <repo> ~/git/dotfiles
cd ~/git/dotfiles
./link.sh        # stow seluruh config ke ~/.config
```

## Kelola
```bash
./link.sh              # link semua
./link.sh hypr         # link satu app
./link.sh uninstall     # buang symlink (file repo utuh)
```

## Tambah app baru
```bash
mv ~/.config/<app> config/<app>
./link.sh <app>
```

Catatan: `config/qutebrowser/autoconfig.yml` di-ignore — di-regenerate oleh tema omarchy (config.py load autoconfig + omarchy.draw).