"""Deliberate failure to prove CI failure reporting. This PR is closed, never merged."""
import unittest


class FailureProbe(unittest.TestCase):
    def test_this_fails_on_purpose(self):
        self.fail("Deliberate failure to prove the Repo status alarm")
