import unittest

from digest.web.app import WebSettings, create_app


class TestWebPayloadBinding(unittest.TestCase):
    def test_payload_endpoints_bind_request_body(self):
        app = create_app(
            WebSettings(
                sources_path="config/sources.yaml",
                sources_overlay_path="data/sources.local.yaml",
                profile_path="config/profile.yaml",
                profile_overlay_path="data/profile.local.yaml",
                db_path="digest-live.db",
                run_lock_path=".runtime/run.lock",
            )
        )
        by_path = {route.path: route for route in app.routes if hasattr(route, "path")}

        for path in [
            "/api/config/sources/add",
            "/api/config/sources/remove",
            "/api/config/profile/validate",
            "/api/config/profile/diff",
            "/api/config/profile/save",
            "/api/config/rollback",
            "/api/onboarding/source-packs/apply",
        ]:
            dependant = by_path[path].dependant
            self.assertIn("payload", [field.name for field in dependant.body_params])
            self.assertNotIn(
                "payload", [field.name for field in dependant.query_params]
            )


if __name__ == "__main__":
    unittest.main()
