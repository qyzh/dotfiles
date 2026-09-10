---
name: omarchy-migrations
description: Write one-time repair migrations for existing Omarchy installs.
version: 0.1.0
author: Omacom (omacom), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, migrations, repair]
    related_skills: []
---

# Omarchy Migrations Skill

Read this before creating or changing migrations under `migrations/`.

Omarchy migrations are one-time repair scripts for existing installs. They are
used when a package update needs to change state that pacman cannot safely own by
itself.

## When to Use

- A package update needs to change user/session state that pacman can't own.
- Existing installs need a one-time repair that survives across users.
- Writing or modifying a script under `migrations/*.sh`.

**Don't use for:** regular package file ownership (pacman handles that), or recurring operations (those belong in hooks, not migrations).

## Migration Model

Migrations live in:
```text
migrations/*.sh
```

They run as the current Omarchy user through `omarchy-migrate`, normally during
`omarchy update`. A migration may touch user/session state (`~/.config`,
`~/.local`, user systemd, browser/editor prefs, DBus/session state), and may also
perform machine-wide repairs when needed.

Completion state is per-user:
```text
~/.local/state/omarchy/migrations/<migration filename>
```

That means every user gets a chance to run every migration. Migrations run as the
user; privileged operations should invoke the appropriate helper or privilege
prompt themselves. Migrations must be idempotent: if one user already applied a
machine-wide repair, the same migration running for another user should detect
that and no-op.

## When Migrations Run

### During `omarchy update`

`omarchy update` is the normal update path. It runs package updates, then:
```bash
omarchy-migrate
omarchy-hook post-update
```

`omarchy-migrate` waits for any active pacman transaction to finish, then runs
all pending migrations for the current user in the visible update terminal.

### At login

Every graphical login starts `omarchy-migrate-notify.service` after
`graphical-session.target`. The notifier checks:
```bash
omarchy-migrate --pending
```

It stays silent while `omarchy update` holds its lock, since that update applies
the pending migrations itself.

If that user has pending migrations, it shows a notification that opens a
terminal for:
```bash
omarchy-migrate
```

The notifier never runs migrations silently in the background.

This is what covers users who did not run the update themselves: someone who
bypassed the pacman guard with `sudo env OMARCHY_ALLOW_DIRECT_PACMAN=1 pacman
-Syu`, and any second user on the machine, whose migration markers are per-user
and therefore still missing after another user updated.

Login is the only trigger on purpose. Watching the packaged migration directory
also fires during a normal `omarchy update`, which prompts for migrations that
`omarchy-migrate` is about to run in the visible update terminal.

### Manually

Users can safely run migrations manually via `omarchy-migrate`.

## Procedure

1. **Write idempotent scripts.** A migration must detect whether its work is already done and no-op if so. This is essential because completion state is per-user — one user's machine-wide repair does not mark it done for others.
2. **Run as the user.** Privileged operations should invoke the appropriate helper or prompt for privilege themselves.
3. **Completion marker.** Write the marker to `~/.local/state/omarchy/migrations/<migration filename>` after successful application.
4. **Test across users.** Verify that a migration applied by one user is detected as already-done by another user for machine-wide repairs.

## Pitfalls

- Assuming a migration runs once per machine — it runs once per user.
- Non-idempotent migrations — a second user running the same migration may re-apply a machine-wide repair.
- Running privileged operations without a helper or privilege prompt.
- Silent background execution — the notifier never runs migrations silently.
