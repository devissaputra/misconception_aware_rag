from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

import pandas as pd
import pyarrow

ROOT = Path(__file__).resolve().parents[1]
REVISION = "2c94ad3e1aafab77146f384e23536f97a4849815"
FILE = "data/test-00000-of-00001.parquet"
EXPECTED_SHA256 = "3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667"
URL = f"https://huggingface.co/datasets/allenai/sciq/resolve/{REVISION}/{FILE}"
LICENSE = "CC BY-NC 3.0"
PAPER = "Welbl, Liu & Gardner (2017), Crowdsourcing Multiple Choice Science Questions, arXiv:1707.06209"

BM25_K1 = 1.5
BM25_B = 0.75
RETRIEVAL_K = 5
BOOTSTRAP_REPLICATES = 3000
BOOTSTRAP_SEED = 20260925
SHUFFLE_SEED = 20260925
TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)

MODES = (
    "question_only",
    "wrong_answer_conditioned",
    "shuffled_wrong_answer_control",
    "oracle_corrective",
)


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text).lower())


def validate_source_hash(payload: bytes, expected_sha256: str = EXPECTED_SHA256) -> str:
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        raise ValueError(
            f"SciQ test parquet SHA-256 mismatch: {digest}; expected {expected_sha256}. "
            "The frozen research protocol requires the exact validated bytes."
        )
    return digest


class BM25Index:
    def __init__(
        self,
        documents: list[tuple[str, str]],
        k1: float = BM25_K1,
        b: float = BM25_B,
    ):
        if not documents:
            raise ValueError("documents must not be empty")
        self.ids = [doc_id for doc_id, _ in documents]
        if len(self.ids) != len(set(self.ids)):
            raise ValueError("document ids must be unique")
        self.k1, self.b = float(k1), float(b)
        self.term_counts: list[Counter[str]] = []
        self.lengths: list[int] = []
        df: Counter[str] = Counter()
        for _, text in documents:
            tok = tokens(text)
            counts = Counter(tok)
            self.term_counts.append(counts)
            self.lengths.append(len(tok))
            df.update(counts.keys())
        self.avg_length = sum(self.lengths) / len(self.lengths)
        n = len(self.ids)
        self.idf = {
            term: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def rank(self, query: str, k: int = RETRIEVAL_K) -> list[str]:
        q = Counter(tokens(query))
        scored: list[tuple[float, str]] = []
        for doc_id, counts, length in zip(self.ids, self.term_counts, self.lengths):
            score = 0.0
            for term, q_count in q.items():
                tf = counts.get(term, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (
                    1.0 - self.b + self.b * length / max(1.0, self.avg_length)
                )
                score += self.idf.get(term, 0.0) * (
                    tf * (self.k1 + 1.0) / denom
                ) * min(q_count, 2)
            scored.append((score, doc_id))
        scored.sort(key=lambda row: (-row[0], row[1]))
        return [doc_id for score, doc_id in scored[:k] if score > 0]


def reciprocal_rank(ranked: list[str], relevant: str) -> float:
    for i, doc_id in enumerate(ranked, start=1):
        if doc_id == relevant:
            return 1.0 / i
    return 0.0


def recall_at(ranked: list[str], relevant: str, k: int) -> float:
    return float(relevant in ranked[:k])


def ndcg_at(ranked: list[str], relevant: str, k: int) -> float:
    try:
        rank = ranked[:k].index(relevant) + 1
    except ValueError:
        return 0.0
    return 1.0 / math.log2(rank + 1)


def download_test(cache_dir: Path) -> tuple[pd.DataFrame, dict]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "sciq-test.parquet"
    if not path.exists():
        with urllib.request.urlopen(URL, timeout=120) as response:
            path.write_bytes(response.read())
    payload = path.read_bytes()
    digest = validate_source_hash(payload)
    frame = pd.read_parquet(path)
    required = {
        "question",
        "distractor1",
        "distractor2",
        "distractor3",
        "correct_answer",
        "support",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"SciQ schema missing fields: {missing}")
    if len(frame) != 1000:
        raise ValueError(f"Unexpected SciQ test row count: {len(frame)}; expected 1000")
    return frame, {
        "dataset": "SciQ",
        "repository": "allenai/sciq",
        "revision": REVISION,
        "file": FILE,
        "url": URL,
        "sha256": digest,
        "license": LICENSE,
        "paper": PAPER,
        "rows_loaded": int(len(frame)),
    }


def build_study(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    eligible = (
        frame[frame["support"].fillna("").str.strip().ne("")]
        .copy()
        .reset_index(drop=True)
    )
    support_to_id: dict[str, str] = {}
    documents: list[tuple[str, str]] = []
    for support in eligible["support"].astype(str):
        key = support.strip()
        if key not in support_to_id:
            doc_id = f"S{len(support_to_id) + 1:04d}"
            support_to_id[key] = doc_id
            documents.append((doc_id, key))
    eligible["relevant_doc"] = [
        support_to_id[str(x).strip()] for x in eligible["support"]
    ]
    return eligible, documents


def _derangement(n: int, rng: random.Random) -> list[int]:
    if n < 2:
        raise ValueError("at least two questions are required for shuffled control")
    candidate = list(range(n))
    for _ in range(1000):
        rng.shuffle(candidate)
        if all(i != candidate[i] for i in range(n)):
            return candidate.copy()
    raise RuntimeError("could not generate deterministic derangement")


def shuffled_wrong_answer_lookup(
    frame: pd.DataFrame,
    seed: int = SHUFFLE_SEED,
) -> dict[tuple[int, int], tuple[int, str]]:
    """Map each case to distractor text from a different question.

    For each distractor position, every eligible question's distractor is used
    exactly once as control text. This preserves the marginal distractor-text
    distribution while breaking the question-answer relationship.
    """
    rng = random.Random(seed)
    n = len(frame)
    lookup: dict[tuple[int, int], tuple[int, str]] = {}
    for d_idx in (1, 2, 3):
        sources = _derangement(n, rng)
        for target_idx, source_idx in enumerate(sources):
            text = str(frame.iloc[source_idx][f"distractor{d_idx}"]).strip()
            lookup[(target_idx, d_idx)] = (int(source_idx), text)
    return lookup


def evaluate(
    frame: pd.DataFrame,
    index: BM25Index,
    shuffle_seed: int = SHUFFLE_SEED,
) -> list[dict]:
    controls = shuffled_wrong_answer_lookup(frame, seed=shuffle_seed)
    cases: list[dict] = []
    for q_idx, row in frame.iterrows():
        question = str(row["question"]).strip()
        correct = str(row["correct_answer"]).strip()
        relevant = str(row["relevant_doc"])
        for d_idx in (1, 2, 3):
            wrong = str(row[f"distractor{d_idx}"]).strip()
            control_source, shuffled_wrong = controls[(int(q_idx), d_idx)]
            queries = {
                "question_only": question,
                "wrong_answer_conditioned": f"{question} {wrong}",
                "shuffled_wrong_answer_control": f"{question} {shuffled_wrong}",
                "oracle_corrective": f"{question} {wrong} {correct}",
            }
            record = {
                "question_id": int(q_idx),
                "distractor_index": d_idx,
                "shuffled_source_question_id": int(control_source),
                "query_token_counts": {
                    mode: len(tokens(query)) for mode, query in queries.items()
                },
            }
            for mode in MODES:
                ranked = index.rank(queries[mode], k=RETRIEVAL_K)
                record[mode] = {
                    "rr": reciprocal_rank(ranked, relevant),
                    "recall_1": recall_at(ranked, relevant, 1),
                    "recall_3": recall_at(ranked, relevant, 3),
                    "recall_5": recall_at(ranked, relevant, 5),
                    "ndcg_5": ndcg_at(ranked, relevant, 5),
                }
            cases.append(record)
    return cases


def aggregate(cases: list[dict]) -> dict:
    metrics = ("rr", "recall_1", "recall_3", "recall_5", "ndcg_5")
    return {
        mode: {
            metric: sum(c[mode][metric] for c in cases) / len(cases)
            for metric in metrics
        }
        for mode in MODES
    }


def aggregate_query_lengths(cases: list[dict]) -> dict[str, float]:
    return {
        mode: sum(c["query_token_counts"][mode] for c in cases) / len(cases)
        for mode in MODES
    }


def question_block_bootstrap(
    cases: list[dict],
    treatment: str,
    comparator: str,
    n_boot: int = BOOTSTRAP_REPLICATES,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    by_question: dict[int, list[float]] = {}
    for case in cases:
        q = case["question_id"]
        delta = case[treatment]["rr"] - case[comparator]["rr"]
        by_question.setdefault(q, []).append(delta)
    blocks = [sum(v) / len(v) for v in by_question.values()]
    observed = sum(blocks) / len(blocks)
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        sample = [blocks[rng.randrange(len(blocks))] for _ in blocks]
        boot.append(sum(sample) / len(sample))
    boot.sort()
    lo = boot[int(0.025 * (len(boot) - 1))]
    hi = boot[int(0.975 * (len(boot) - 1))]
    return {
        "unit": "question",
        "metric": f"mean reciprocal rank delta ({treatment} minus {comparator})",
        "treatment": treatment,
        "comparator": comparator,
        "n_questions": len(blocks),
        "n_bootstrap": n_boot,
        "bootstrap_seed": seed,
        "mean_delta": observed,
        "bootstrap_95_interval": [lo, hi],
    }


def directional_analysis(
    cases: list[dict],
    treatment: str,
    comparator: str,
) -> dict:
    improve = worse = tie = 0
    for case in cases:
        a = case[treatment]["rr"]
        b = case[comparator]["rr"]
        if a > b:
            improve += 1
        elif a < b:
            worse += 1
        else:
            tie += 1
    return {
        "treatment": treatment,
        "comparator": comparator,
        "improved_cases": improve,
        "worsened_cases": worse,
        "tied_cases": tie,
    }


def build_results_latex(result: dict) -> str:
    bs = "\\"
    row_end = bs + bs
    labels = {
        "question_only": "Question only",
        "wrong_answer_conditioned": "Observed wrong answer",
        "shuffled_wrong_answer_control": "Shuffled wrong-answer control",
        "oracle_corrective": "Oracle-informed corrective",
    }
    lines = [
        f"{bs}section{{Generated empirical results}}",
        "This section is generated by \\texttt{scripts/run\_sciq\_study.py}; numerical values should not be hand-edited.",
        "",
        f"Frozen SciQ revision: \\texttt{{{result['dataset']['revision']}}}; "
        f"eligible questions: {result['design']['eligible_questions_with_support']}; "
        f"wrong-answer proxy cases: {result['design']['wrong_answer_cases']}.",
        "",
        f"{bs}begin{{table}}[htbp]",
        f"{bs}centering",
        f"{bs}small",
        f"{bs}begin{{tabular}}{{lrrrrr}}",
        f"{bs}toprule",
        "Condition & MRR & R@1 & R@3 & R@5 & nDCG@5 " + row_end,
        f"{bs}midrule",
    ]
    for mode in MODES:
        m = result["metrics"][mode]
        lines.append(
            f"{labels[mode]} & {m['rr']:.4f} & {m['recall_1']:.4f} & "
            f"{m['recall_3']:.4f} & {m['recall_5']:.4f} & {m['ndcg_5']:.4f} " + row_end
        )
    lines += [
        f"{bs}bottomrule",
        f"{bs}end{{tabular}}",
        f"{bs}caption{{SciQ support-passage retrieval under the four frozen query conditions.}}",
        f"{bs}end{{table}}",
        "",
    ]
    for key, label in (
        ("wrong_vs_question", "Observed wrong answer minus question-only"),
        ("shuffled_vs_question", "Shuffled control minus question-only"),
        ("wrong_vs_shuffled", "Observed wrong answer minus shuffled control"),
    ):
        d = result["uncertainty"][key]
        lo, hi = d["bootstrap_95_interval"]
        lines.append(
            f"{label}: mean MRR delta {d['mean_delta']:.4f}, "
            f"question-block bootstrap 95\\% interval [{lo:.4f}, {hi:.4f}]."
        )
    lines += [
        "",
        "The shuffled control preserves the marginal distractor-text distribution while breaking the question--answer relation. It is a lexical-expansion negative control, not a simulated learner response.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(
    meta: dict,
    frame: pd.DataFrame,
    documents: list[tuple[str, str]],
    cases: list[dict],
    summary: dict,
    uncertainty: dict,
    directional: dict,
) -> dict:
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    result = {
        "research_bundle": True,
        "status": "complete",
        "dataset": meta,
        "protocol": {
            "bm25": {"k1": BM25_K1, "b": BM25_B},
            "retrieval_k": RETRIEVAL_K,
            "tokenizer_regex": TOKEN_RE.pattern,
            "tokenizer_flags": "UNICODE; lowercase",
            "bootstrap_replicates": uncertainty["wrong_vs_question"]["n_bootstrap"],
            "bootstrap_seed_primary": uncertainty["wrong_vs_question"]["bootstrap_seed"],
            "shuffle_seed": SHUFFLE_SEED,
            "shuffled_control": (
                "within each distractor position, a deterministic no-self-match permutation "
                "assigns distractor text from another eligible question"
            ),
            "shuffled_control_preserves_marginal_distractor_texts": True,
        },
        "design": {
            "eligible_questions_with_support": int(len(frame)),
            "unique_support_documents": int(len(documents)),
            "wrong_answer_cases": int(len(cases)),
            "conditions": {
                "question_only": "question text only",
                "wrong_answer_conditioned": (
                    "question plus one SciQ distractor as an observed wrong-answer proxy"
                ),
                "shuffled_wrong_answer_control": (
                    "question plus distractor text drawn by deterministic derangement "
                    "from a different eligible question"
                ),
                "oracle_corrective": (
                    "question plus observed distractor plus gold correct answer; "
                    "oracle-informed sensitivity condition only"
                ),
            },
            "primary_comparison": "wrong_answer_conditioned versus question_only",
            "negative_control_comparison": (
                "wrong_answer_conditioned versus shuffled_wrong_answer_control"
            ),
            "important_nonclaim": "SciQ distractors are not validated learner misconceptions",
        },
        "metrics": summary,
        "mean_query_tokens": aggregate_query_lengths(cases),
        "uncertainty": uncertainty,
        "directional_error_analysis": directional,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "pandas": pd.__version__,
            "pyarrow": pyarrow.__version__,
            "platform": platform.platform(),
        },
    }
    (out / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    rows = []
    for case in cases:
        for mode in MODES:
            rows.append(
                {
                    "question_id": case["question_id"],
                    "distractor_index": case["distractor_index"],
                    "shuffled_source_question_id": (
                        case["shuffled_source_question_id"]
                        if mode == "shuffled_wrong_answer_control"
                        else ""
                    ),
                    "condition": mode,
                    "query_tokens": case["query_token_counts"][mode],
                    **case[mode],
                }
            )
    pd.DataFrame(rows).to_csv(out / "per_case_metrics.csv", index=False)

    lines = [
        "# Empirical Results Summary",
        "",
        "Generated by `scripts/run_sciq_study.py`; numerical values should not be hand-edited.",
        "",
        "## External dataset",
        "",
        f"- SciQ test rows loaded: {meta['rows_loaded']}",
        f"- Eligible questions with support paragraphs: {len(frame)}",
        f"- Unique support documents in retrieval corpus: {len(documents)}",
        f"- Wrong-answer proxy cases: {len(cases)}",
        f"- Pinned revision: `{meta['revision']}`",
        f"- Source parquet SHA-256: `{meta['sha256']}`",
        f"- License: {meta['license']}",
        "",
        "## Frozen retrieval protocol",
        "",
        f"- BM25 k1 / b: {BM25_K1} / {BM25_B}",
        f"- retrieval depth: {RETRIEVAL_K}",
        f"- bootstrap replicates: {uncertainty['wrong_vs_question']['n_bootstrap']}",
        f"- shuffled-control seed: {SHUFFLE_SEED}",
        "",
        "## Retrieval results",
        "",
        "| Condition | MRR | Recall@1 | Recall@3 | Recall@5 | nDCG@5 | Mean query tokens |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    query_lengths = result["mean_query_tokens"]
    for mode in MODES:
        m = summary[mode]
        lines.append(
            f"| {mode} | {m['rr']:.4f} | {m['recall_1']:.4f} | "
            f"{m['recall_3']:.4f} | {m['recall_5']:.4f} | {m['ndcg_5']:.4f} | "
            f"{query_lengths[mode]:.2f} |"
        )

    lines += ["", "## Paired question-block uncertainty", ""]
    for key, label in (
        ("wrong_vs_question", "Observed wrong answer − question only"),
        ("shuffled_vs_question", "Shuffled wrong-answer control − question only"),
        ("wrong_vs_shuffled", "Observed wrong answer − shuffled wrong-answer control"),
    ):
        d = uncertainty[key]
        lines.append(
            f"- {label}: mean MRR delta {d['mean_delta']:.4f}; "
            f"95% interval [{d['bootstrap_95_interval'][0]:.4f}, "
            f"{d['bootstrap_95_interval'][1]:.4f}]"
        )

    lines += ["", "## Directional analysis", ""]
    for key, label in (
        ("wrong_vs_question", "Observed wrong answer vs question only"),
        ("wrong_vs_shuffled", "Observed wrong answer vs shuffled control"),
    ):
        d = directional[key]
        lines.append(
            f"- {label}: improved / worsened / tied = "
            f"{d['improved_cases']} / {d['worsened_cases']} / {d['tied_cases']}"
        )

    lines += [
        "",
        "## Interpretation boundary",
        "",
        "SciQ distractors are crowdsourced incorrect answer options, not expert-validated learner misconception labels. The shuffled condition is a lexical-expansion negative control: it preserves the marginal distractor-text distribution while intentionally breaking the question–answer relationship. The gold-answer condition is oracle-informed sensitivity analysis, not a mathematical upper bound and not a deployable method.",
        "",
    ]

    text = "\n".join(lines)
    (out / "summary.md").write_text(text, encoding="utf-8")

    paper = ROOT / "paper"
    paper.mkdir(exist_ok=True)
    (paper / "results.md").write_text(text, encoding="utf-8")
    (paper / "results.tex").write_text(build_results_latex(result), encoding="utf-8")
    return result


def run_study(
    cache_dir: Path,
    bootstrap_replicates: int = BOOTSTRAP_REPLICATES,
) -> dict:
    frame, meta = download_test(cache_dir)
    eligible, documents = build_study(frame)
    index = BM25Index(documents, k1=BM25_K1, b=BM25_B)
    cases = evaluate(eligible, index, shuffle_seed=SHUFFLE_SEED)
    summary = aggregate(cases)
    uncertainty = {
        "wrong_vs_question": question_block_bootstrap(
            cases,
            "wrong_answer_conditioned",
            "question_only",
            n_boot=bootstrap_replicates,
            seed=BOOTSTRAP_SEED,
        ),
        "shuffled_vs_question": question_block_bootstrap(
            cases,
            "shuffled_wrong_answer_control",
            "question_only",
            n_boot=bootstrap_replicates,
            seed=BOOTSTRAP_SEED + 1,
        ),
        "wrong_vs_shuffled": question_block_bootstrap(
            cases,
            "wrong_answer_conditioned",
            "shuffled_wrong_answer_control",
            n_boot=bootstrap_replicates,
            seed=BOOTSTRAP_SEED + 2,
        ),
    }
    directional = {
        "wrong_vs_question": directional_analysis(
            cases, "wrong_answer_conditioned", "question_only"
        ),
        "wrong_vs_shuffled": directional_analysis(
            cases, "wrong_answer_conditioned", "shuffled_wrong_answer_control"
        ),
    }
    return write_outputs(
        meta,
        eligible,
        documents,
        cases,
        summary,
        uncertainty,
        directional,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data" / "cache")
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP_REPLICATES)
    args = parser.parse_args()
    result = run_study(args.cache_dir, bootstrap_replicates=args.bootstrap)
    print(
        json.dumps(
            {
                "dataset": result["dataset"],
                "metrics": result["metrics"],
                "uncertainty": result["uncertainty"],
                "directional": result["directional_error_analysis"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
