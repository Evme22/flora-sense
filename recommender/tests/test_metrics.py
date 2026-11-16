import pandas as pd
import pytest

from training.metrics import dcg_at_k, ndcg_at_k, deterministic_group_split


def test_dcg_uses_log2_discount():
    assert dcg_at_k([3, 2, 0], 3) == pytest.approx(7 + 3 / 1.58496250072)


def test_ndcg_perfect_order():
    frame = pd.DataFrame({"group_id": [1, 1, 1], "target": [3, 2, 0], "pred": [0.9, 0.8, 0.1]})
    assert ndcg_at_k(frame, "pred", 3) == pytest.approx(1.0)


def test_group_split_disjoint():
    train, val = deterministic_group_split([1, 1, 2, 3, 4, 5], seed=123)
    assert train.isdisjoint(val)
    assert train | val == {1, 2, 3, 4, 5}
