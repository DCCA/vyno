from __future__ import annotations

import re
from pathlib import Path
import unittest

import yaml


class TestDockerAssets(unittest.TestCase):
    def test_compose_bot_command_includes_profile_overlay(self) -> None:
        compose = yaml.safe_load(Path("compose.yaml").read_text(encoding="utf-8"))
        command = compose["services"]["digest-bot"]["command"]
        self.assertIn("--sources-overlay", command)
        self.assertIn("data/sources.local.yaml", command)
        self.assertIn("--profile-overlay", command)
        self.assertIn("data/profile.local.yaml", command)

    def test_compose_healthcheck_uses_bot_health_command(self) -> None:
        compose = yaml.safe_load(Path("compose.yaml").read_text(encoding="utf-8"))
        health_test = compose["services"]["digest-bot"]["healthcheck"]["test"]
        self.assertGreaterEqual(len(health_test), 3)
        self.assertEqual(health_test[0], "CMD")
        self.assertIn("bot-health-check", health_test)

    def test_makefile_runtime_targets_include_overlays(self) -> None:
        data = Path("Makefile").read_text(encoding="utf-8")
        self.assertRegex(
            data,
            r"(?m)^live:\n\t.*--sources-overlay data/sources\.local\.yaml .*--profile-overlay data/profile\.local\.yaml .* run$",
        )
        self.assertRegex(
            data,
            r"(?m)^schedule:\n\t.*--sources-overlay data/sources\.local\.yaml .*--profile-overlay data/profile\.local\.yaml .* schedule ",
        )
        self.assertRegex(
            data,
            r"(?m)^bot:\n\t.*--sources-overlay data/sources\.local\.yaml .*--profile-overlay data/profile\.local\.yaml .* bot$",
        )

    def test_dockerfile_default_cmd_includes_profile_overlay(self) -> None:
        data = Path("Dockerfile").read_text(encoding="utf-8")
        self.assertRegex(data, r'CMD \["--sources".*"--sources-overlay".*"--profile".*"--profile-overlay".*"bot"\]')


if __name__ == "__main__":
    unittest.main()
