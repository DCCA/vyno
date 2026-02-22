import argparse
import unittest
from unittest.mock import patch

from digest.cli import _cmd_admin_streamlit_prototype


class TestAdminStreamlitPrototype(unittest.TestCase):
    def test_cmd_admin_streamlit_prototype_invokes_streamlit(self):
        args = argparse.Namespace(host="127.0.0.1", port=8790)
        with patch("subprocess.run") as run_mock:
            _cmd_admin_streamlit_prototype(args)
        called = run_mock.call_args
        self.assertIsNotNone(called)
        cmd = called.args[0]
        self.assertEqual(cmd[0], "streamlit")
        self.assertIn("src/digest/admin_streamlit/prototype.py", cmd)


if __name__ == "__main__":
    unittest.main()
