import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from misconception_aware_rag import core


class CoreTests(unittest.TestCase):
    def test_retrieval_prefers_relevant_evidence(self):
        results = core.retrieve("light energy", {"a": "light energy", "b": "water cycle"}, 2)
        self.assertEqual([row[1] for row in results], ["a"])

    def test_grounded_response_does_not_fill_with_zero_overlap_docs(self):
        result = core.grounded_response("photosynthesis light", {"d1": "light energy", "d2": "tectonic plates"}, {})
        self.assertEqual(result["evidence_ids"], ["d1"])


if __name__ == "__main__":
    unittest.main()
