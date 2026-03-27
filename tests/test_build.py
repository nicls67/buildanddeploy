import runpy
import sys
import unittest
from unittest.mock import patch
from io import StringIO

class TestBuildPy(unittest.TestCase):
    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['build.py', '-h'])
    def test_display_help(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            runpy.run_path('build.py')
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("BuildAndDeploy version", mock_stdout.getvalue())
        self.assertIn("Usage: build.py <working_directory>", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['build.py'])
    def test_bad_argument(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            runpy.run_path('build.py')
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: Bad argument supplied", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('sys.argv', ['build.py', 'non_existent_directory_12345'])
    def test_invalid_directory(self, mock_stdout):
        with self.assertRaises(SystemExit) as cm:
            runpy.run_path('build.py')
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error: The given path is not a valid directory.", mock_stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
