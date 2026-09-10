---
name: omarchy-visual-verification
description: Visually verify Omarchy UI changes in the running shell.
version: 0.1.0
author: Omacom (omacom), Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [omarchy, visual, verification, screenshots]
    related_skills: []
---

# Omarchy Visual Verification Skill

Read this before finishing any change with a visual effect: Omarchy shell
styling and layout, panels, menus, notifications, desktop appearance,
animations, transitions, screenshots, and screen recording flows.

Visual changes must be verified in the running UI in addition to automated
tests. Creating an artifact is not sufficient: inspect it for clipping,
overlap, incorrect spacing, stale state, focus problems, and visual
regressions before finishing.

## When to Use

- Finishing a change to shell styling, layout, panels, menus, or notifications.
- Changing animations, transitions, or screen capture/recording flows.
- Verifying a visual change before marking work complete.

**Don't use for:** automated test assertions (those are separate), or non-visual logic changes.

## Quick Reference

```bash
# Full-screen screenshot without opening the editor:
omarchy capture screenshot fullscreen save

# Interactive smart-region screenshot:
omarchy screenshot

# Short full-screen video for animation/transition/timing changes:
omarchy screenrecord --fullscreen
# Exercise the changed behavior.
omarchy screenrecord --stop-recording
```

## Procedure

1. **Capture reference and candidate states as separate images** when changing a layer-shell surface or layout, then compare both.
2. **Inspect the artifact.** Check for clipping, overlap, incorrect spacing, stale state, focus problems, and visual regressions. Creating the screenshot/recording is not sufficient — you must look at it.
3. **For animation/transition/timing changes, record a short video** rather than a single frame. Review the recording before finishing, and keep it short and focused on the changed behavior.
4. **For interactive UI work, use `wtype`** to simulate keyboard input when available. Example: start the UI in the background, wait briefly for focus, then run `wtype -k Right -k Return` to exercise keyboard selection and confirm the resulting command output or state change. Prefer this over manual-only verification when a UI returns a selected value or changes a symlink/config.
5. **Clean up.** If a launched UI would otherwise remain open, keep track of its PID and stop it after the screenshot or recording; avoid broad process kills unless checking with `ps` first.

## Pitfalls

- Treating a captured screenshot as proof of correctness without inspecting it.
- Using a single frame to verify animation or transition changes.
- Leaving launched UIs running after verification.
- Broad process kills to clean up — check `ps` first.
