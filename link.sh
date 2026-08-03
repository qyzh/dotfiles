#!/usr/bin/env bash
# Dotfiles manager — GNU Stow
# Usage:
#   ./link.sh          link all configs into ~/.config
#   ./link.sh <app>    link one app
#   ./link.sh unlink    remove all symlinks (files stay in repo)
set -euo pipefail
cd "$(dirname "$0")"

if [ "${1:-}" = "uninstall" ]; then
    stow -t "$HOME/.config" -d "$PWD" -D config
    echo "Unlinked all. Files tetap di repo."
    exit 0
fi

apps="${1:-config}"
stow -t "$HOME/.config" -d "$PWD" "$apps"
echo "Linked: $apps"