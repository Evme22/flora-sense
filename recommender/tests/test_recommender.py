"""Behavior tests for the original content-based ranking algorithm."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from prototype.bouquet_recommender_v1 import (
    dominant_color_score,
    flower_bonus_score,
    recommend_bouquets,
)

DATASET = Path(__file__).resolve().parents[1] / "data" / "demo_bouquets.xlsx"
PROFILE = {
    "gender": "female",
    "age_group": "adult",
    "favorite_colors": ["pink", "white"],
    "favorite_flowers": ["роза", "эустома"],
    "unwanted_flowers": ["лилия"],
    "occasion": "birthday",
    "style": "romantic",
}


def test_color_priority():
    assert dominant_color_score(["pink"], "pink", "white", ["pink", "white"]) > dominant_color_score(
        ["pink"], "white", "pink", ["pink", "white"]
    )


def test_flower_bonus_soft_preference():
    assert flower_bonus_score(["роза", "эустома"], ["роза", "эустома"]) == 1.0
    assert flower_bonus_score(["роза", "эустома"], ["роза"]) == 0.6
    assert flower_bonus_score(["роза"], ["ромашка"]) == 0.0


def test_excluded_flowers_and_top_n():
    ranked = recommend_bouquets(DATASET, PROFILE, top_n=4)
    assert 0 < len(ranked) <= 4
    assert all("лилия" not in flowers for flowers in ranked["flowers"])
    assert ranked["score"].is_monotonic_decreasing


def test_api_works_offline():
    client = TestClient(app)
    assert client.get("/health").json() == {"ok": True}
    response = client.post("/recommend", json={**PROFILE, "top_n": 3})
    assert response.status_code == 200
    data = response.json()["items"]
    assert len(data) == 3
    assert all("score" in item for item in data)
    assert all("лилия" not in item["flowers"] for item in data)


def test_api_rejects_invalid_top_n():
    response = TestClient(app).post("/recommend", json={**PROFILE, "top_n": 0})
    assert response.status_code == 422
