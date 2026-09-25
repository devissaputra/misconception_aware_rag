import hashlib
import json
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_sciq_study as study


class SciQStudyTests(unittest.TestCase):
    def fixture_frame(self):
        return pd.DataFrame(
            {
                "question": ["q0 alpha", "q1 beta", "q2 gamma", "q3 delta"],
                "distractor1": ["a0", "a1", "a2", "a3"],
                "distractor2": ["b0", "b1", "b2", "b3"],
                "distractor3": ["c0", "c1", "c2", "c3"],
                "correct_answer": ["z0", "z1", "z2", "z3"],
                "support": [
                    "alpha evidence",
                    "beta evidence",
                    "gamma evidence",
                    "delta evidence",
                ],
            }
        )

    def test_frozen_source_hash_guard(self):
        payload = b"sciq-fixture"
        expected = hashlib.sha256(payload).hexdigest()
        self.assertEqual(study.validate_source_hash(payload, expected), expected)
        with self.assertRaises(ValueError):
            study.validate_source_hash(payload, "0" * 64)

    def test_build_study_deduplicates_support_documents(self):
        frame = self.fixture_frame()
        frame.loc[3, "support"] = frame.loc[2, "support"]
        eligible, documents = study.build_study(frame)
        self.assertEqual(len(eligible), 4)
        self.assertEqual(len(documents), 3)
        self.assertEqual(
            eligible.loc[2, "relevant_doc"],
            eligible.loc[3, "relevant_doc"],
        )

    def test_shuffled_control_has_no_self_matches_and_preserves_text_multiset(self):
        frame = self.fixture_frame()
        lookup = study.shuffled_wrong_answer_lookup(frame, seed=17)
        for d_idx in (1, 2, 3):
            sources = []
            texts = []
            for q_idx in range(len(frame)):
                source_idx, text = lookup[(q_idx, d_idx)]
                self.assertNotEqual(q_idx, source_idx)
                sources.append(source_idx)
                texts.append(text)
            self.assertEqual(sorted(sources), list(range(len(frame))))
            self.assertEqual(
                sorted(texts),
                sorted(frame[f"distractor{d_idx}"].astype(str).tolist()),
            )

    def test_evaluate_includes_negative_control_without_raw_text(self):
        frame, documents = study.build_study(self.fixture_frame())
        index = study.BM25Index(documents)
        cases = study.evaluate(frame, index, shuffle_seed=17)
        self.assertEqual(len(cases), 12)
        case = cases[0]
        for mode in study.MODES:
            self.assertIn(mode, case)
            self.assertIn("rr", case[mode])
        self.assertNotIn("question", case)
        self.assertNotIn("support", case)
        self.assertNotEqual(
            case["question_id"],
            case["shuffled_source_question_id"],
        )

    def test_question_block_bootstrap_uses_question_as_resampling_unit(self):
        cases = []
        for q in range(3):
            for d in range(3):
                cases.append(
                    {
                        "question_id": q,
                        "wrong_answer_conditioned": {"rr": 0.5 + 0.1 * q},
                        "question_only": {"rr": 0.5},
                    }
                )
        result = study.question_block_bootstrap(
            cases,
            "wrong_answer_conditioned",
            "question_only",
            n_boot=100,
            seed=1,
        )
        self.assertEqual(result["n_questions"], 3)
        self.assertEqual(result["n_bootstrap"], 100)
        self.assertAlmostEqual(result["mean_delta"], 0.1)

    def test_committed_empirical_evidence_matches_frozen_protocol(self):
        metrics = json.loads(
            (ROOT / "results" / "metrics.json").read_text(encoding="utf-8")
        )
        self.assertTrue(metrics["research_bundle"])
        self.assertEqual(metrics["status"], "complete")
        self.assertEqual(metrics["dataset"]["revision"], study.REVISION)
        self.assertEqual(metrics["dataset"]["sha256"], study.EXPECTED_SHA256)
        self.assertEqual(metrics["dataset"]["rows_loaded"], 1000)
        self.assertEqual(
            metrics["design"]["eligible_questions_with_support"],
            884,
        )
        self.assertEqual(metrics["design"]["wrong_answer_cases"], 2652)
        self.assertEqual(
            metrics["protocol"]["bm25"],
            {"k1": study.BM25_K1, "b": study.BM25_B},
        )
        self.assertEqual(metrics["protocol"]["retrieval_k"], study.RETRIEVAL_K)
        self.assertEqual(metrics["protocol"]["shuffle_seed"], study.SHUFFLE_SEED)
        self.assertIn("shuffled_wrong_answer_control", metrics["metrics"])
        self.assertIn("wrong_vs_shuffled", metrics["uncertainty"])
        self.assertIn("environment", metrics)

        header = (
            ROOT / "results" / "per_case_metrics.csv"
        ).read_text(encoding="utf-8").splitlines()[0]
        self.assertNotIn("question,", header)
        self.assertNotIn("support", header)
        self.assertIn("shuffled_source_question_id", header)

        generated_tex = (
            ROOT / "paper" / "results.tex"
        ).read_text(encoding="utf-8")
        self.assertIn("Generated empirical results", generated_tex)
        self.assertIn("Shuffled wrong-answer control", generated_tex)


if __name__ == "__main__":
    unittest.main()
