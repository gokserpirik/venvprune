import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import venvprune


class ScanTests(unittest.TestCase):
    def test_finds_environments_sorted_by_size_and_skips_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, content in (("project/.venv", "12345"), ("other", "1"), ("node_modules/hidden", "123456")):
                path = root / name
                path.mkdir(parents=True)
                (path / "pyvenv.cfg").write_text(content)
            found = venvprune.find_venvs(root)
            self.assertEqual([path for path, _ in found], [root / "project/.venv", root / "other"])

    def test_does_not_follow_directory_symlinks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            env = root / "env"
            env.mkdir()
            (env / "pyvenv.cfg").touch()
            (root / ".venv").symlink_to(env, target_is_directory=True)
            self.assertEqual([path for path, _ in venvprune.find_venvs(root)], [env])

    def test_scan_root_cannot_be_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "pyvenv.cfg").touch()
            with patch("sys.argv", ["venvprune", str(root)]), \
                 patch("venvprune.questionary.checkbox") as checkbox, \
                 patch("venvprune.questionary.confirm") as confirm:
                checkbox.return_value.ask.return_value = [str(root)]
                confirm.return_value.ask.side_effect = [True, False]
                venvprune.main()
            self.assertTrue(root.is_dir())
            self.assertTrue((root / "pyvenv.cfg").exists())

    def test_format_size(self):
        self.assertEqual(venvprune.format_size(1024), "1.0 KB")


class DeletionTests(unittest.TestCase):
    def test_selection_confirmation_and_safety(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            scan = root / "scan"
            scan.mkdir()
            first, second, outside = scan / "first", scan / "second", root / "outside"
            for path in (first, second, outside):
                path.mkdir()
                (path / "pyvenv.cfg").touch()

            def run(selections, confirmations):
                with patch("sys.argv", ["venvprune", str(scan)]), \
                     patch("venvprune.questionary.checkbox") as checkbox, \
                     patch("venvprune.questionary.confirm") as confirm, \
                     redirect_stdout(StringIO()) as output:
                    checkbox.return_value.ask.side_effect = selections
                    confirm.return_value.ask.side_effect = confirmations
                    venvprune.main()
                    return output.getvalue()

            run([None], [])
            run([[]], [])
            run([[str(first)]], [False, False])
            self.assertTrue(first.exists())
            run([[str(first)], [str(second)]], [False, True, True, False])
            self.assertTrue(first.exists())
            self.assertFalse(second.exists())

            link = scan / "link"
            link.symlink_to(outside, target_is_directory=True)
            (first / "pyvenv.cfg").unlink()
            sentinel = scan / "sentinel"
            sentinel.mkdir()
            (sentinel / "pyvenv.cfg").touch()
            output = run([[str(scan), str(outside), str(link), str(first)]], [True, False])
            self.assertEqual(output.count("Skipped unsafe path:"), 4)
            self.assertTrue(scan.exists())
            self.assertTrue(outside.exists())
            self.assertTrue(link.is_symlink())
            self.assertTrue(first.exists())


if __name__ == "__main__":
    unittest.main()
