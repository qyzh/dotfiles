"""Tests for scripts/sources.py (stdlib unittest; no pytest needed).

Run:  python3 -m unittest discover -s skills/research/grounded-citations/tests -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "sources.py"


class SourcesCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "hermes-home"
        self.env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("SOURCES_LEDGER", "HERMES_CITATION_LEDGER")
        }
        # Isolate the legacy default ledger ($HERMES_HOME/cache/citations/ledger.json).
        self.env["HERMES_HOME"] = str(self.home)
        self.env["PYTHONPATH"] = ""  # never import a real hermes_constants
        self.default_ledger = self.home / "cache" / "citations" / "ledger.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-I", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            env=env or self.env,
            cwd=self.tmp,
        )

    def draft(self, body: str) -> Path:
        path = self.tmp / "post.md"
        path.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
        return path

    def ledger_with(self, n: int) -> Path:
        ledger = self.tmp / "out" / ".sources-post-2026-11-19.json"
        for i in range(1, n + 1):
            r = self.run_cli("--ledger", str(ledger), "add", f"https://example.com/s{i}", "--title", f"S{i}")
            self.assertEqual(r.returncode, 0, r.stderr)
        return ledger

    # -- ledger selection --------------------------------------------------

    def test_add_auto_inits_fresh_ledger_without_reset(self) -> None:
        ledger = self.tmp / "nested" / "dir" / ".sources-x-2026-11-19.json"
        self.assertFalse(ledger.exists())
        r = self.run_cli("add", "--ledger", str(ledger), "https://example.com/a", "--title", "A")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "[1] https://example.com/a")
        data = json.loads(ledger.read_text())
        self.assertEqual(data["version"], 1)
        self.assertEqual([s["id"] for s in data["sources"]], [1])
        self.assertFalse(self.default_ledger.exists(), "per-post add must not touch the global ledger")

    def test_add_auto_inits_zero_byte_ledger(self) -> None:
        ledger = self.tmp / "empty.json"
        ledger.write_text("")
        r = self.run_cli("--ledger", str(ledger), "add", "https://example.com/a")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "[1] https://example.com/a")

    def test_ledger_flag_accepted_on_every_subcommand(self) -> None:
        ledger = self.tmp / "l.json"
        d = self.draft("Water is wet.[1]\n")
        for args in (
            ("reset",),
            ("add", "https://example.com/a"),
            ("list",),
            ("render",),
            ("render", "--replace-in", str(d)),
            ("verify", str(d)),
        ):
            r = self.run_cli(*args, "--ledger", str(ledger))
            self.assertEqual(r.returncode, 0, f"{args}: {r.stdout}{r.stderr}")
        self.assertFalse(self.default_ledger.exists())

    def test_sources_ledger_env_fallback(self) -> None:
        ledger = self.tmp / "env.json"
        env = dict(self.env, SOURCES_LEDGER=str(ledger), HERMES_CITATION_LEDGER=str(self.tmp / "other.json"))
        r = self.run_cli("add", "https://example.com/a", env=env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(ledger.exists())
        self.assertFalse((self.tmp / "other.json").exists())
        # An explicit --ledger still beats the env var.
        explicit = self.tmp / "explicit.json"
        r = self.run_cli("--ledger", str(explicit), "add", "https://example.com/b", env=env)
        self.assertEqual(r.stdout.strip(), "[1] https://example.com/b")

    def test_backward_compat_default_ledger_when_flag_omitted(self) -> None:
        r = self.run_cli("reset")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(str(self.default_ledger), r.stdout)
        self.assertEqual(self.run_cli("add", "https://example.com/a").stdout.strip(), "[1] https://example.com/a")
        self.assertEqual(self.run_cli("add", "https://example.com/b/").stdout.strip(), "[2] https://example.com/b")
        self.assertEqual(len(json.loads(self.default_ledger.read_text())["sources"]), 2)
        # Legacy env var still honoured when --ledger and SOURCES_LEDGER are absent.
        legacy = self.tmp / "legacy.json"
        env = dict(self.env, HERMES_CITATION_LEDGER=str(legacy))
        self.assertEqual(self.run_cli("add", "https://example.com/z", env=env).stdout.strip(), "[1] https://example.com/z")
        self.assertTrue(legacy.exists())
        # Default verify keeps v1 semantics: an uncited ledger entry is only a warning.
        d = self.draft("Only the first source backs this claim.[1]\n")
        self.assertEqual(self.run_cli("render", "--replace-in", str(d)).returncode, 0)
        r = self.run_cli("verify", str(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("warn: registered in the ledger but not cited in this draft: [2]", r.stdout)

    # -- verify ------------------------------------------------------------

    def test_orphan_citation_fails_with_line_and_sentence(self) -> None:
        ledger = self.ledger_with(1)
        d = self.draft(
            """
            # Title

            Supported claim here.[1]
            This one cites a source that was never registered.[7] Another sentence.
            """
        )
        self.run_cli("--ledger", str(ledger), "render", "--replace-in", str(d))
        r = self.run_cli("--ledger", str(ledger), "verify", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn(
            'FAIL: line 4: orphan citation [7] is not in the ledger (hallucinated or renumbered): '
            '"This one cites a source that was never registered.[7]"',
            r.stderr,
        )

    def test_uncited_ledger_entry_fails_with_require_all_cited(self) -> None:
        ledger = self.ledger_with(3)
        d = self.draft("Claim one.[1]\n\nClaim three.[3]\n")
        self.run_cli("--ledger", str(ledger), "render", "--replace-in", str(d))
        r = self.run_cli("--ledger", str(ledger), "verify", "--require-all-cited", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL: ledger source [2] https://example.com/s2 — S2 is never cited in the draft", r.stderr)
        self.assertNotIn("[1] https://example.com/s1", r.stderr)
        # Fully cited draft passes.
        d.write_text("Claim one.[1]\n\nClaim two.[2] Claim three.[3]\n")
        self.run_cli("--ledger", str(ledger), "render", "--replace-in", str(d))
        r = self.run_cli("--ledger", str(ledger), "verify", "--require-all-cited", str(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_uncited_numeric_sentence_warns_then_fails_under_strict(self) -> None:
        ledger = self.ledger_with(1)
        d = self.draft(
            """
            # Title

            Adoption reached 42% of teams last year.[1]
            Costs fell to $3.5 million after the migration. Latency improved
            by 3x once caching landed.

            - About 12,000 developers answered the survey.
            - The product shipped in 2025 on Python 3.12, a GPT-4 class model.
            """
        )
        self.run_cli("--ledger", str(ledger), "render", "--replace-in", str(d))
        r = self.run_cli("--ledger", str(ledger), "verify", str(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        out = r.stdout
        self.assertIn('warn: line 4: statistic without a [n] citation: "Costs fell to $3.5 million after the migration."', out)
        self.assertIn('warn: line 4: statistic without a [n] citation: "Latency improved by 3x once caching landed."', out)
        self.assertIn('warn: line 7: statistic without a [n] citation: "About 12,000 developers answered the survey."', out)
        self.assertNotIn("42%", out)  # cited sentence
        self.assertNotIn("Python 3.12", out)  # years / versions are not statistics

        r = self.run_cli("--ledger", str(ledger), "verify", "--strict", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn('FAIL: line 4: statistic without a [n] citation: "Costs fell to $3.5 million', r.stderr)

    def test_citation_after_period_stays_with_its_sentence(self) -> None:
        ledger = self.ledger_with(1)
        d = self.draft("Share rose to 40%.[1] Revenue hit Rp 15.000 per user.\n")
        self.run_cli("--ledger", str(ledger), "render", "--replace-in", str(d))
        r = self.run_cli("--ledger", str(ledger), "verify", str(d))
        self.assertIn('line 1: statistic without a [n] citation: "Revenue hit Rp 15.000 per user."', r.stdout)
        self.assertNotIn("Share rose", r.stdout)

    def test_unrestored_cite_token_fails(self) -> None:
        ledger = self.ledger_with(1)
        d = self.draft("Fine.[1]\n\nHumanizer left this token behind.[[CITE_1]]\n")
        self.run_cli("--ledger", str(ledger), "render", "--replace-in", str(d))
        r = self.run_cli("--ledger", str(ledger), "verify", str(d))
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL: line 3: unrestored placeholder [[CITE_1]]", r.stderr)

    def test_html_comments_and_frontmatter_are_ignored(self) -> None:
        ledger = self.ledger_with(1)
        d = self.draft(
            """
            ---
            title: Example 50% [9]
            ---
            # Title

            Claim.[1]

            <!-- Populate from the Balance block: 30% of [8]
                 keep every [n] tag intact. -->
            """
        )
        self.run_cli("--ledger", str(ledger), "render", "--replace-in", str(d))
        r = self.run_cli("--ledger", str(ledger), "verify", "--strict", "--require-all-cited", str(d))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
