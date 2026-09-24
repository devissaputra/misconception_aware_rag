import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from misconception_aware_rag import core


def documents():
    return [
        core.EvidenceDocument(
            "D1",
            "plant respiration",
            "counterevidence",
            "Plant cells perform cellular respiration in mitochondria.",
            authority=1.0,
        ),
        core.EvidenceDocument(
            "D2",
            "photosynthesis",
            "explanation",
            "Photosynthesis converts light energy into chemical energy.",
            authority=1.0,
        ),
        core.EvidenceDocument(
            "D3",
            "plant respiration",
            "remediation",
            "Compare photosynthesis with cellular respiration: plants do both processes.",
            authority=0.9,
        ),
        core.EvidenceDocument(
            "D4",
            "tectonics",
            "definition",
            "Tectonic plates move over geological time.",
            authority=1.0,
        ),
    ]


def catalog():
    return [
        core.MisconceptionRecord(
            misconception_id="M1",
            concept="plant respiration",
            canonical_statement="Plants do not respire.",
            description="Confuses photosynthesis with absence of respiration.",
            positive_cues=(
                "plants do not respire",
                "only animals respire",
            ),
            negative_cues=(
                "it is false that plants do not respire",
                "plants do respire",
            ),
            corrective_concepts=(
                "cellular respiration",
                "mitochondria",
            ),
            remediation="Contrast photosynthesis and respiration.",
            evidence_ids=("D1", "D3"),
        )
    ]


class CoreTests(unittest.TestCase):
    def test_document_validation(self):
        with self.assertRaises(ValueError):
            core.EvidenceDocument(
                "D1", "x", "mystery", "text"
            )

    def test_authority_validation(self):
        with self.assertRaises(ValueError):
            core.EvidenceDocument(
                "D1", "x", "definition", "text", authority=2
            )

    def test_misconception_requires_positive_cues(self):
        with self.assertRaises(ValueError):
            core.MisconceptionRecord(
                "M1", "x", "statement", "desc", ()
            )

    def test_unicode_tokenization_retrieves(self):
        docs = [
            core.EvidenceDocument(
                "D1",
                "correlación",
                "explanation",
                "La correlación no demuestra causación.",
            )
        ]
        result = core.retrieve_generic(
            "correlación causación",
            docs,
            1,
        )
        self.assertEqual(result[0]["doc_id"], "D1")

    def test_detects_possible_misconception(self):
        result = core.detect_misconceptions(
            "Only animals respire.",
            catalog(),
        )
        self.assertEqual(result[0]["status"], "possible")
        self.assertEqual(result[0]["misconception_id"], "M1")

    def test_rejection_cue_prevents_false_positive(self):
        result = core.detect_misconceptions(
            "It is false that plants do not respire.",
            catalog(),
        )
        self.assertEqual(result[0]["status"], "ambiguous")
        self.assertNotEqual(result[0]["status"], "possible")

    def test_explicit_correct_statement_is_rejected(self):
        result = core.detect_misconceptions(
            "Plants do respire.",
            catalog(),
        )
        self.assertEqual(result[0]["status"], "rejected")

    def test_no_detection_for_unrelated_response(self):
        self.assertEqual(
            core.detect_misconceptions(
                "Plants need light.",
                catalog(),
            ),
            [],
        )

    def test_query_is_conditioned_on_misconception(self):
        detections = core.detect_misconceptions(
            "Only animals respire.",
            catalog(),
        )
        query = core.build_retrieval_query(
            "Do plants respire?",
            "Only animals respire.",
            detections,
        )
        self.assertIn("cellular respiration", query)
        self.assertIn("mitochondria", query)

    def test_generic_bm25_discards_zero_overlap(self):
        result = core.retrieve_generic(
            "plant respiration",
            documents(),
            4,
        )
        ids = [row["doc_id"] for row in result]
        self.assertNotIn("D4", ids)

    def test_generic_retrieval_rejects_boolean_k(self):
        with self.assertRaises(ValueError):
            core.retrieve_generic(
                "plant",
                documents(),
                True,
            )

    def test_duplicate_document_ids_rejected(self):
        docs = documents()
        docs.append(
            core.EvidenceDocument(
                "D1",
                "other",
                "definition",
                "duplicate",
            )
        )
        with self.assertRaises(ValueError):
            core.retrieve_generic("plant", docs)

    def test_misconception_evidence_changes_retrieval(self):
        result = core.retrieve_misconception_aware(
            "Do plants respire?",
            "Only animals respire.",
            documents(),
            catalog(),
            k=3,
        )
        ids = [row["doc_id"] for row in result["results"]]
        self.assertIn("D1", ids)
        self.assertIn("D3", ids)

    def test_retrieval_exposes_score_breakdown(self):
        result = core.retrieve_misconception_aware(
            "Do plants respire?",
            "Only animals respire.",
            documents(),
            catalog(),
            k=2,
        )
        row = result["results"][0]
        self.assertIn("bm25_score", row)
        self.assertIn("misconception_boost", row)
        self.assertIn("kind_boost", row)

    def test_rejected_misconception_does_not_activate_boost(self):
        result = core.retrieve_misconception_aware(
            "Do plants respire?",
            "Plants do respire.",
            documents(),
            catalog(),
            k=3,
        )
        self.assertFalse(
            any(
                row["misconception_boost"] >= 0.85
                for row in result["results"]
            )
        )

    def test_evidence_sufficiency_passes_with_two_passages(self):
        result = core.retrieve_misconception_aware(
            "Do plants respire?",
            "Only animals respire.",
            documents(),
            catalog(),
            k=3,
        )
        status = core.assess_evidence_sufficiency(
            result,
            min_documents=2,
            min_top_score=0.1,
        )
        self.assertTrue(status["sufficient"])

    def test_evidence_sufficiency_abstains_when_empty(self):
        status = core.assess_evidence_sufficiency(
            {"results": [], "detections": []},
            min_documents=1,
            min_top_score=0.1,
        )
        self.assertFalse(status["sufficient"])

    def test_generation_is_citation_grounded(self):
        result = core.retrieve_misconception_aware(
            "Do plants respire?",
            "Only animals respire.",
            documents(),
            catalog(),
            k=3,
        )
        response = core.generate_grounded_tutor_response(
            "Do plants respire?",
            "Only animals respire.",
            result,
            min_documents=2,
            min_top_score=0.1,
        )
        self.assertEqual(
            response["status"],
            "grounded_response",
        )
        for citation in response["citations"]:
            self.assertIn(f"[{citation}]", response["response"])

    def test_generation_labels_possible_not_certain(self):
        result = core.retrieve_misconception_aware(
            "Do plants respire?",
            "Only animals respire.",
            documents(),
            catalog(),
            k=3,
        )
        response = core.generate_grounded_tutor_response(
            "Do plants respire?",
            "Only animals respire.",
            result,
            min_documents=2,
            min_top_score=0.1,
        )
        self.assertIn("possible misconception", response["response"])

    def test_generation_abstains_on_insufficient_evidence(self):
        response = core.generate_grounded_tutor_response(
            "Question",
            "Learner response",
            {"results": [], "detections": []},
            min_documents=1,
            min_top_score=0.1,
        )
        self.assertEqual(response["status"], "abstain")

    def test_precision_recall_f1_perfect(self):
        metrics = core.precision_recall_f1(
            ["M1"], ["M1"]
        )
        self.assertEqual(metrics["f1"], 1.0)

    def test_precision_recall_f1_handles_empty_expected(self):
        metrics = core.precision_recall_f1([], [])
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 1.0)

    def test_retrieval_metrics_perfect_top_two(self):
        metrics = core.retrieval_metrics(
            ["D1", "D3", "D2"],
            ["D1", "D3"],
            k=2,
        )
        self.assertEqual(metrics["precision_at_k"], 1.0)
        self.assertEqual(metrics["recall_at_k"], 1.0)
        self.assertEqual(metrics["reciprocal_rank"], 1.0)
        self.assertAlmostEqual(metrics["ndcg_at_k"], 1.0)

    def test_retrieval_metrics_penalizes_late_hit(self):
        metrics = core.retrieval_metrics(
            ["D2", "D1"],
            ["D1"],
            k=2,
        )
        self.assertEqual(metrics["reciprocal_rank"], 0.5)

    def test_evaluate_case_runs_end_to_end(self):
        result = core.evaluate_case(
            "Do plants respire?",
            "Only animals respire.",
            documents(),
            catalog(),
            ["M1"],
            ["D1", "D3"],
            k=3,
        )
        self.assertEqual(
            result["predicted_misconceptions"],
            ["M1"],
        )
        self.assertGreater(
            result["retrieval_metrics"]["recall_at_k"],
            0,
        )

    def test_load_documents_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "docs.csv"
            path.write_text(
                "doc_id,concept,kind,text,source,authority\n"
                "D1,plants,definition,Plants respire.,course,1.0\n",
                encoding="utf-8",
            )
            loaded = core.load_documents_csv(path)
            self.assertEqual(loaded[0].doc_id, "D1")

    def test_load_catalog_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.csv"
            path.write_text(
                "misconception_id,concept,canonical_statement,description,"
                "positive_cues,negative_cues,corrective_concepts,remediation,evidence_ids\n"
                "M1,plants,Plants do not respire.,desc,"
                "plants do not respire,plants do respire,"
                "cellular respiration,contrast,D1\n",
                encoding="utf-8",
            )
            loaded = core.load_catalog_csv(path)
            self.assertEqual(loaded[0].misconception_id, "M1")

    def test_legacy_retrieve_prefers_relevant_evidence(self):
        results = core.retrieve(
            "light energy",
            {"a": "light energy", "b": "water cycle"},
            2,
        )
        self.assertEqual([row[1] for row in results], ["a"])

    def test_legacy_grounded_response_drops_zero_overlap(self):
        result = core.grounded_response(
            "photosynthesis light",
            {
                "d1": "light energy",
                "d2": "tectonic plates",
            },
            {},
        )
        self.assertEqual(result["evidence_ids"], ["d1"])


if __name__ == "__main__":
    unittest.main()
