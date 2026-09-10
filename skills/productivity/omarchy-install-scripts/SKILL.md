---
name: omarchy-install-scripts
description: Write target-side setup and install leaves for Omarchy.
version: 0.1.0
author: Omacom (omacom), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, install, setup]
    related_skills: []
---

# Omarchy Install Scripts Skill

Read this before working under `install/` or on the system/user setup commands.

The ISO owns installation orchestration. This repo ships target-side setup
commands and reusable setup leaves:

- `bin/omarchy-apply-system` runs root-owned system setup during ISO finalization.
- `bin/omarchy-apply-hardware` runs idempotent hardware-specific setup and is called by `omarchy-apply-system`.
- `bin/omarchy-finalize-user` runs the per-user runtime finalization (skill symlinks, xdg-user-dirs, mime defaults, `install/user/all.sh`). Shipped user defaults are seeded by `/etc/skel` from `omarchy-settings`, not by this command. `bin/omarchy-reinstall-configs` is the explicit destructive resync of those defaults into an existing user's `$HOME`.
- Leaf scripts under `install/` are sourced by `run_logged $OMARCHY_INSTALL/path/to/script.sh` and intentionally do not have shebangs.
- Avoid `exit` in sourced setup scripts unless intentionally aborting setup.
- Use `$OMARCHY_INSTALL` and `$OMARCHY_PATH` instead of hard-coded Omarchy paths.
- Keep root-scoped hardware setup under `install/hardware/` and orchestrate it through `install/hardware/all.sh`.
- Keep every per-user setup leaf under `install/user/` (including `install/user/hardware/` and `install/user/first-run/`) so it is clear what must run for each user.
- Prefer helper commands for package and command checks where available.

Raw `command -v`, `pacman`, and `pacman-key` are acceptable in package-helper
contexts where direct package-manager behavior is the point of the script.

## When to Use

- Writing a leaf script under `install/`.
- Modifying `bin/omarchy-apply-system`, `bin/omarchy-apply-hardware`, or `bin/omarchy-finalize-user`.
- Reviewing or refactoring existing install/setup code.

**Don't use for:** ISO orchestration (that lives in the sibling `omarchy-iso` repo), or application-level installers unrelated to Omarchy setup.

## Procedure

1. **Place the leaf correctly.** Per-user setup → `install/user/`. Root-scoped hardware → `install/hardware/`, orchestrated through `install/hardware/all.sh`.
2. **No shebang on leaf scripts.** Leaves are sourced, not executed directly.
3. **No `exit`** unless intentionally aborting setup.
4. **Use variables, not hard-coded paths.** `$OMARCHY_INSTALL` and `$OMARCHY_PATH` for Omarchy paths.
5. **Prefer helper commands** for package and command checks where available; fall back to raw `command -v`, `pacman`, `pacman-key` only in package-helper contexts where direct package-manager behavior is the point.

## Pitfalls

- Adding `exit` to a sourced leaf — aborts the whole setup chain.
- Hard-coding `/usr`, `/etc`, or Omarchy paths instead of using the provided variables.
- Putting per-user logic under `install/hardware/` or root logic under `install/user/`.
- Giving a leaf script a shebang — it's sourced, not run.
