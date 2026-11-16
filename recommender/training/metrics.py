from __future__ import annotations

import hashlib
import math
from typing import Iterable

import pandas as pd


def deterministic_group_split(group_ids: Iterable[int], val_ratio: float = 0.2, seed: int = 42) -> tuple[set[int], set[int]]:
    unique_ids = sorted({int(group_id) for group_id in group_ids})

    if not unique_ids:
        return set(), set()

    scored = []

    for group_id in unique_ids:
        digest = hashlib.md5(f"{seed}:{group_id}".encode("utf-8")).hexdigest()
        scored.append((digest, group_id))

    scored.sort()
    val_count = max(1, int(round(len(unique_ids) * val_ratio))) if len(unique_ids) > 1 else 0
    val_ids = {group_id for _, group_id in scored[:val_count]}
    train_ids = {group_id for group_id in unique_ids if group_id not in val_ids}

    if not train_ids and val_ids:
        moved = next(iter(val_ids))
        val_ids.remove(moved)
        train_ids.add(moved)

    return train_ids, val_ids


def dcg_at_k(labels: list[float], k: int) -> float:
    total = 0.0

    for index, label in enumerate(labels[:k], start=1):
        total += (2**label - 1) / math.log2(index + 1)

    return total


def ndcg_at_k(frame: pd.DataFrame, score_column: str, k: int) -> float:
    group_scores = []

    for _, group in frame.groupby("group_id"):
        predicted = group.sort_values(score_column, ascending=False)["target"].tolist()
        ideal = sorted(group["target"].tolist(), reverse=True)
        ideal_dcg = dcg_at_k(ideal, k)

        if ideal_dcg <= 0:
            continue

        group_scores.append(dcg_at_k(predicted, k) / ideal_dcg)

    if not group_scores:
        return 0.0

    return float(sum(group_scores) / len(group_scores))


def hit_rate_at_k(frame: pd.DataFrame, score_column: str, k: int) -> float:
    hits = []

    for _, group in frame.groupby("group_id"):
        top_k = group.sort_values(score_column, ascending=False).head(k)
        hits.append(float((top_k["target"] > 0).any()))

    if not hits:
        return 0.0

    return float(sum(hits) / len(hits))


def reciprocal_rank_at_k(frame: pd.DataFrame, score_column: str, k: int) -> float:
    values = []

    for _, group in frame.groupby("group_id"):
        ranked = group.sort_values(score_column, ascending=False).head(k)
        reciprocal = 0.0

        for index, label in enumerate(ranked["target"].tolist(), start=1):
            if label > 0:
                reciprocal = 1.0 / index
                break

        values.append(reciprocal)

    if not values:
        return 0.0

    return float(sum(values) / len(values))


def summarize_ranking_metrics(frame: pd.DataFrame, score_column: str) -> dict[str, float]:
    return {
        "ndcg@5": ndcg_at_k(frame, score_column, 5),
        "ndcg@10": ndcg_at_k(frame, score_column, 10),
        "hit_rate@5": hit_rate_at_k(frame, score_column, 5),
        "mrr@10": reciprocal_rank_at_k(frame, score_column, 10),
    }
