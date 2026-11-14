"""Every relative link in the repository's Markdown points at a file that exists."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from check_doc_links import broken_links


class DocLinkTests(unittest.TestCase):
    def test_no_dead_relative_links(self):
        self.assertEqual(broken_links(), [])


if __name__ == '__main__':
    unittest.main()
