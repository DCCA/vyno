import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from digest.web.app import (
    DEFAULT_WEB_CORS_ORIGINS,
    WebSettings,
    _cors_allow_origin_regex,
    _cors_allowed_origins,
    create_app,
)


class TestWebCors(unittest.TestCase):
    def test_default_origins_match_expected(self):
        with patch.dict("os.environ", {"DIGEST_WEB_CORS_ORIGINS": ""}, clear=False):
            self.assertEqual(_cors_allowed_origins(), DEFAULT_WEB_CORS_ORIGINS)

    def test_default_regex_allows_local_and_private_networks(self):
        with patch.dict(
            "os.environ", {"DIGEST_WEB_CORS_ORIGIN_REGEX": ""}, clear=False
        ):
            pattern = re.compile(_cors_allow_origin_regex())

        allowed = [
            "http://localhost:5173",
            "http://127.0.0.1:5174",
            "http://0.0.0.0:3000",
            "http://192.168.1.24:5173",
            "http://10.0.0.5:8787",
            "http://172.16.0.2:8080",
            "http://172.31.255.255:6553",
        ]
        blocked = [
            "http://172.32.0.1:8080",
            "https://example.com",
            "http://malicious.site:5173",
        ]

        for origin in allowed:
            self.assertIsNotNone(
                pattern.fullmatch(origin),
                f"expected origin to match: {origin}",
            )

        for origin in blocked:
            self.assertIsNone(
                pattern.fullmatch(origin),
                f"expected origin to be blocked: {origin}",
            )

    def test_env_overrides_origins_and_regex(self):
        with patch.dict(
            "os.environ",
            {
                "DIGEST_WEB_CORS_ORIGINS": "https://a.example, https://b.example",
                "DIGEST_WEB_CORS_ORIGIN_REGEX": r"^https://override\.example$",
            },
            clear=False,
        ):
            self.assertEqual(
                _cors_allowed_origins(),
                ["https://a.example", "https://b.example"],
            )
            self.assertEqual(_cors_allow_origin_regex(), r"^https://override\.example$")

    def test_create_app_wires_cors_regex_for_dynamic_ports(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            app = create_app(
                WebSettings(
                    sources_path=str(root / "config" / "sources.yaml"),
                    sources_overlay_path=str(tmp_path / "sources.local.yaml"),
                    profile_path=str(root / "config" / "profile.yaml"),
                    profile_overlay_path=str(tmp_path / "profile.local.yaml"),
                    db_path=str(tmp_path / "digest.db"),
                    run_lock_path=str(tmp_path / "run.lock"),
                )
            )

        cors = next(
            (m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"), None
        )
        self.assertIsNotNone(cors)
        regex = str(cors.kwargs.get("allow_origin_regex", ""))
        self.assertTrue(regex)
        self.assertIsNotNone(re.fullmatch(regex, "http://127.0.0.1:5174"))


if __name__ == "__main__":
    unittest.main()
