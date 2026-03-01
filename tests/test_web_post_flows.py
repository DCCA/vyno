import tempfile
import unittest
from pathlib import Path

from digest.web.app import WebSettings, create_app


class TestWebPostFlows(unittest.TestCase):
    def _app(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            settings = WebSettings(
                sources_path=str(root / "config" / "sources.yaml"),
                sources_overlay_path=str(tmp_path / "sources.local.yaml"),
                profile_path=str(root / "config" / "profile.yaml"),
                profile_overlay_path=str(tmp_path / "profile.local.yaml"),
                db_path=str(tmp_path / "digest.db"),
                run_lock_path=str(tmp_path / "run.lock"),
                history_dir=str(tmp_path / "history"),
                onboarding_state_path=str(tmp_path / "onboarding-state.json"),
            )
            yield create_app(settings)

    def test_post_payload_routes_use_plain_dict_body(self):
        for app in self._app():
            routes = [route for route in app.routes if getattr(route, "path", None)]

            def _post_route(path: str):
                for route in routes:
                    methods = set(getattr(route, "methods", set()) or set())
                    if str(getattr(route, "path")) == path and "POST" in methods:
                        return route
                raise KeyError(path)

            for path in [
                "/api/config/sources/add",
                "/api/config/sources/remove",
                "/api/config/profile/validate",
                "/api/config/profile/diff",
                "/api/config/profile/save",
                "/api/config/rollback",
                "/api/onboarding/source-packs/apply",
                "/api/timeline/notes",
            ]:
                route = _post_route(path)
                dependant = getattr(route, "dependant")
                self.assertEqual(len(dependant.body_params), 1)
                body_param = dependant.body_params[0]
                self.assertEqual(body_param.name, "payload")
                self.assertEqual(
                    str(getattr(body_param.field_info, "annotation", "")),
                    "dict[str, typing.Any]",
                )

    def test_source_pack_apply_endpoint_callable_with_dict_payload(self):
        for app in self._app():
            routes = [route for route in app.routes if getattr(route, "path", None)]
            endpoint = None
            for route in routes:
                methods = set(getattr(route, "methods", set()) or set())
                if (
                    str(getattr(route, "path")) == "/api/onboarding/source-packs/apply"
                    and "POST" in methods
                ):
                    endpoint = getattr(route, "endpoint")
                    break
            self.assertIsNotNone(endpoint)
            result = endpoint(payload={"pack_id": "quickstart-core"})
            self.assertIn("added_count", result)
            self.assertIn("existing_count", result)


if __name__ == "__main__":
    unittest.main()
