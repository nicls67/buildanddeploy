# pyright: reportAny=false, reportExplicitAny=false
import runpy
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch


class TestBuildPy(unittest.TestCase):
    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["build.py", "-h"])
    def test_display_help(self, mock_stdout: MagicMock) -> None:
        with self.assertRaises(SystemExit) as cm:
            _ = runpy.run_path("build.py")
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("BuildAndDeploy version", str(mock_stdout.getvalue()))  # type: ignore
        self.assertIn(
            "Usage: build.py <working_directory>", str(mock_stdout.getvalue())  # type: ignore
        )

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["build.py"])
    def test_bad_argument(self, mock_stdout: MagicMock) -> None:
        with self.assertRaises(SystemExit) as cm:
            _ = runpy.run_path("build.py")
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: Bad argument supplied", str(mock_stdout.getvalue()))  # type: ignore

    @patch("sys.stdout", new_callable=StringIO)
    @patch("sys.argv", ["build.py", "non_existent_directory_12345"])
    def test_invalid_directory(self, mock_stdout: MagicMock) -> None:
        with self.assertRaises(SystemExit) as cm:
            _ = runpy.run_path("build.py")
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(
            "Error: The given path is not a valid directory.",
            str(mock_stdout.getvalue()),  # type: ignore
        )


if __name__ == "__main__":
    _ = unittest.main()
