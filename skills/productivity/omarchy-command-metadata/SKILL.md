---
name: omarchy-command-metadata
description: Declare CLI metadata in comments for bin/ commands.
version: 0.1.0
author: Omacom (omacom), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, cli, metadata]
    related_skills: []
---

# Omarchy Command Metadata Skill

Read this before adding or changing commands in `bin/`.

Commands in `bin/` can declare CLI metadata in comments near the top of the
file. `bin/omarchy` scans the first 80 lines, and tests expect command metadata
to remain valid.

## When to Use

- Adding a new command to `bin/`.
- Changing the summary, args, or examples of an existing command.
- Adding aliases or hiding a command from default listings.

**Don't use for:** scripts outside `bin/`, or metadata-heavy docs that aren't command metadata.

## Supported Metadata Keys

| Key | Purpose |
|---|---|
| `# omarchy:group=...` | Override the command group inferred from filename |
| `# omarchy:name=...` | Override the command name inferred from filename |
| `# omarchy:summary=...` | Short help text |
| `# omarchy:args=...` | Usage arguments |
| `# omarchy:examples=...` | Examples separated with ` | ` |
| `# omarchy:alias=...` / `# omarchy:aliases=...` | Alternate routes |
| `# omarchy:hidden=true` | Hide from default command listings |
| `# omarchy:requires-sudo=true` | Mark commands that require sudo |

Only use `omarchy:examples` where there are args that need explaining.

## Procedure

1. Place metadata comments within the first 80 lines of the file.
2. Keep routes consistent with the filename unless there is a deliberate alias or compatibility route.
3. Prefer explicit metadata for user-facing commands.

## Example

```bash
# omarchy:summary=Take a screenshot
# omarchy:args=[smart|region|windows|fullscreen] [slurp|copy]
# omarchy:examples=omarchy screenshot | omarchy capture screenshot region
```

## Pitfalls

- Metadata placed after line 80 — `bin/omarchy` won't scan it.
- Adding `omarchy:examples` when there are no args to explain — unnecessary noise.
- Inconsistent alias routes that don't match the filename convention without a deliberate reason.

## Verification

Run the command metadata tests (expected by the project) to confirm metadata is valid and scanned correctly.
