from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import urllib.request
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REVISION = "2c94ad3e1aafab77146f384e23536f97a4849815"
FILE = "data/test-00000-of-00001.parquet"
EXPECTED_SHA256 = "3a719356a29b127fc54ef3c7f51a034db4bd105d5717215e8c85d2aa58d60667"
URL = f"https://huggingface.co/datasets/allenai/sciq/resolve/{REVISION}/{FILE}"
LICENSE = "CC BY-NC 3.0"
PAPER = "Welbl, Liu & Gardner (2017), Crowdsourcing Multiple Choice Science Questions, arXiv:1707.06209"
TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(str(text).lower())


class BM25Index:
    def __init__(self, documents: list[tuple[str, str]], k1: float = 1.5, b: float = 0.75):
        if not documents:
            raise ValueError("documents must not be empty")
        self.ids = [doc_id for doc_id, _ in documents]
        if len(self.ids) != len(set(self.ids)):
            raise ValueError("document ids must be unique")
        self.k1, self.b = float(k1), float(b)
        self.term_counts = []
        self.lengths = []
        df = Counter()
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

    def rank(self, query: str, k: int = 5) -> list[str]:
        q = Counter(tokens(query))
        scored = []
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
    digest = hashlib.sha256(payload).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"SciQ test parquet SHA-256 mismatch: {digest}")
    frame = pd.read_parquet(path)
    required = {"question", "distractor1", "distractor2", "distractor3", "correct_answer", "support"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"SciQ schema missing fields: {missing}")
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


def build_study(frame: pd.DataFrame):
    eligible = frame[frame["support"].fillna("").str.strip().ne("")].copy().reset_index(drop=True)
    support_to_id = {}
    documents = []
    for support in eligible["support"].astype(str):
        key = support.strip()
        if key not in support_to_id:
            doc_id = f"S{len(support_to_id)+1:04d}"
            support_to_id[key] = doc_id
            documents.append((doc_id, key))
    eligible["relevant_doc"] = [support_to_id[str(x).strip()] for x in eligible["support"]]
    return eligible, documents


def evaluate(frame: pd.DataFrame, index: BM25Index):
    cases = []
    modes = ("question_only", "wrong_answer_conditioned", "oracle_corrective")
    for q_idx, row in frame.iterrows():
        question = str(row["question"]).strip()
        correct = str(row["correct_answer"]).strip()
        relevant = str(row["relevant_doc"])
        for d_idx in (1, 2, 3):
            wrong = str(row[f"distractor{d_idx}"]).strip()
            queries = {
                "question_only": question,
                "wrong_answer_conditioned": f"{question} {wrong}",
                "oracle_corrective": f"{question} {wrong} {correct}",
            }
            record = {"question_id": int(q_idx), "distractor_index": d_idx}
            for mode in modes:
                ranked = index.rank(queries[mode], k=5)
                record[mode] = {
                    "rr": reciprocal_rank(ranked, relevant),
                    "recall_1": recall_at(ranked, relevant, 1),
                    "recall_3": recall_at(ranked, relevant, 3),
                    "recall_5": recall_at(ranked, relevant, 5),
                    "ndcg_5": ndcg_at(ranked, relevant, 5),
                }
            cases.append(record)
    return cases


def aggregate(cases):
    modes = ("question_only", "wrong_answer_conditioned", "oracle_corrective")
    metrics = ("rr", "recall_1", "recall_3", "recall_5", "ndcg_5")
    out = {}
    for mode in modes:
        out[mode] = {
            metric: sum(c[mode][metric] for c in cases) / len(cases)
            for metric in metrics
        }
    return out


def question_block_bootstrap(cases, n_boot: int = 3000, seed: int = 20260925):
    by_question = {}
    for case in cases:
        q = case["question_id"]
        delta = case["wrong_answer_conditioned"]["rr"] - case["question_only"]["rr"]
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
        "metric": "mean reciprocal rank delta (wrong-answer-conditioned minus question-only)",
        "n_questions": len(blocks),
        "n_bootstrap": n_boot,
        "mean_delta": observed,
        "bootstrap_95_interval": [lo, hi],
    }


def directional_error_analysis(cases):
    improve = worse = tie = 0
    for case in cases:
        a = case["wrong_answer_conditioned"]["rr"]
        b = case["question_only"]["rr"]
        if a > b:
            improve += 1
        elif a < b:
            worse += 1
        else:
            tie += 1
    return {"improved_cases": improve, "worsened_cases": worse, "tied_cases": tie}


def write_outputs(meta, frame, documents, cases, summary, uncertainty, directional):
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    result = {
        "research_bundle": True,
        "dataset": meta,
        "design": {
            "eligible_questions_with_support": int(len(frame)),
            "unique_support_documents": int(len(documents)),
            "wrong_answer_cases": int(len(cases)),
            "conditions": {
                "question_only": "question text only",
                "wrong_answer_conditioned": "question plus one SciQ distractor as an observed wrong-answer proxy",
                "oracle_corrective": "question plus distractor plus gold correct answer; upper-bound sensitivity only",
            },
            "primary_comparison": "wrong_answer_conditioned versus question_only",
            "important_nonclaim": "SciQ distractors are not validated learner misconceptions",
        },
        "metrics": summary,
        "uncertainty": uncertainty,
        "directional_error_analysis": directional,
    }
    (out / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    rows = []
    for case in cases:
        for mode in ("question_only", "wrong_answer_conditioned", "oracle_corrective"):
            rows.append({
                "question_id": case["question_id"],
                "distractor_index": case["distractor_index"],
                "condition": mode,
                **case[mode],
            })
    pd.DataFrame(rows).to_csv(out / "per_case_metrics.csv", index=False)

    lines = [
        "# Empirical Results Summary", "",
        "This file is generated by `scripts/run_sciq_study.py`. It uses real external SciQ data; the small CSV files under `data/` remain software-test fixtures only.", "",
        "## External dataset", "",
        f"- SciQ test rows loaded: {meta['rows_loaded']}",
        f"- Eligible questions with support paragraphs: {len(frame)}",
        f"- Unique support documents in retrieval corpus: {len(documents)}",
        f"- Wrong-answer proxy cases: {len(cases)}",
        f"- Pinned revision: `{meta['revision']}`",
        f"- Source parquet SHA-256: `{meta['sha256']}`",
        f"- License: {meta['license']}", "",
        "## Retrieval results", "",
        "| Condition | MRR | Recall@1 | Recall@3 | Recall@5 | nDCG@5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in ("question_only", "wrong_answer_conditioned", "oracle_corrective"):
        m = summary[mode]
        lines.append(
            f"| {mode} | {m['rr']:.4f} | {m['recall_1']:.4f} | {m['recall_3']:.4f} | {m['recall_5']:.4f} | {m['ndcg_5']:.4f} |"
        )
    lines += [
        "",
        "## Primary paired uncertainty", "",
        f"- Mean MRR delta, wrong-answer-conditioned minus question-only: {uncertainty['mean_delta']:.4f}",
        f"- Question-block bootstrap 95% interval: [{uncertainty['bootstrap_95_interval'][0]:.4f}, {uncertainty['bootstrap_95_interval'][1]:.4f}]",
        f"- Cases improved / worsened / tied: {directional['improved_cases']} / {directional['worsened_cases']} / {directional['tied_cases']}", "",
        "## Interpretation boundary", "",
        "SciQ distractors are crowdsourced incorrect answer options, not expert-validated learner misconception labels. This study tests retrieval conditioning on observable wrong answers. The oracle-corrective condition uses the gold correct answer and is an upper-bound sensitivity analysis, not a deployable method.", "",
    ]
    text = "\n".join(lines)
    (out / "summary.md").write_text(text, encoding="utf-8")
    paper = ROOT / "paper"
    paper.mkdir(exist_ok=True)
    (paper / "results.md").write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data" / "cache")
    parser.add_argument("--bootstrap", type=int, default=3000)
    args = parser.parse_args()

    frame, meta = download_test(args.cache_dir)
    eligible, documents = build_study(frame)
    index = BM25Index(documents)
    cases = evaluate(eligible, index)
    summary = aggregate(cases)
    uncertainty = question_block_bootstrap(cases, n_boot=args.bootstrap)
    directional = directional_error_analysis(cases)
    write_outputs(meta, eligible, documents, cases, summary, uncertainty, directional)
    print(json.dumps({"dataset": meta, "metrics": summary, "uncertainty": uncertainty, "directional": directional}, indent=2))


if __name__ == "__main__":
    main()
