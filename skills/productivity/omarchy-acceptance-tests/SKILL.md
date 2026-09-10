---
name: omarchy-acceptance-tests
description: Run Omarchy's graphical acceptance test suite in a disposable VM.
version: 0.1.0
author: Omacom (omacom), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, testing, acceptance]
    related_skills: []
---

# Omarchy Acceptance Tests Skill

Read this before writing or running the graphical acceptance suite under
`test/acceptance.d/`.

## When to Use

- Writing or modifying a test under `test/acceptance.d/*-test.sh`.
- Running the acceptance suite against an Omarchy ISO.
- Debugging a failing acceptance test.

**Don't use for:** unit tests, shell linting, or anything that doesn't exercise a real installed Omarchy desktop.

## Prerequisites

- Disposable VM available (via the sibling `omarchy-iso` repository).
- ISO built or base installed per the workflow below.

## Quick Reference

```bash
# Reuse an installed base and sync the suite:
cd ../omarchy-iso
./bin/omarchy-iso-test release/<iso>.iso --reuse-base --sync-omarchy ../omarchy --no-preview

# Full fresh build + test (for package manifest / install / defaults changes):
cd ../omarchy-iso
./bin/omarchy-iso-make --no-boot-offer --local-source ../omarchy ../omarchy-pkgs
./bin/omarchy-iso-test release/<generated-iso>.iso --no-preview
```

## Procedure

1. **Choose the right path.** For acceptance-test-only changes, reuse an installed base with `--reuse-base --sync-omarchy`. For changes to package manifests, installation, finalization, or shipped defaults, build fresh and test without `--reuse-base`.
2. **Keep unrelated workflows in separate test files.** The runner records a failed file and continues with remaining files, preserving diagnostic coverage.
3. **Restore modified user state.** Use traps, close anything the test opens, and capture every visually distinct state (including entered input) as `success-<step>.png`. Failure helpers capture `failure-<step>.png`.
4. **Compositor-level shortcuts.** The ISO harness exercises these with QMP virtual keyboard input. In-guest `wtype` is suitable for typing into focused controls but does NOT reliably prove that a global Hyprland keybinding works.

## Pitfalls

- Running acceptance tests in the active development session instead of a disposable VM. The suite opens/closes applications and temporarily changes desktop configuration.
- Trusting `wtype` to prove global Hyprland keybindings — it cannot.
- Leaving modified user state uncleaned after a test run.

## Verification

After a run, check the timestamped `test-runs/` directory for collected screenshots and logs. Open screenshots unless `--no-preview` was passed.
