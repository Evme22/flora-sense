"""Thin adapter exposing the original ranking algorithm with synthetic demo data.

Unlike the production adapter, this version has no image store, backend or DB dependencies.
"""
from pathlib import Path
import pandas as pd

from app.schemas import RecommendationRequest
from prototype.bouquet_recommender_v1 import recommend_bouquets

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "demo_bouquets.xlsx"


def recommend_demo(request: RecommendationRequest) -> list[dict]:
    preferences = {
        "gender": request.gender,
        "age_group": request.age_group,
        "favorite_colors": request.favorite_colors,
        "favorite_flowers": request.favorite_flowers,
        "unwanted_flowers": request.unwanted_flowers,
        "occasion": request.occasion,
        "style": request.style,
    }
    ranked = recommend_bouquets(
        file_path=DATA_FILE,
        user_profile=preferences,
        top_n=request.top_n,
    )
    result = []
    for item in ranked.to_dict(orient="records"):
        result.append({
            key: ("" if pd.isna(value) else value)
            for key, value in item.items()
            if key != "filename"
        })
    return result
