"""Standalone public demo of the Flora Sense production baseline recommender."""
from fastapi import FastAPI

from app.adapter import recommend_demo
from app.schemas import RecommendationRequest, RecommendationResponse

app = FastAPI(
    title="Flora Sense · Recommendation Demo",
    description="Public demo of the content-based bouquet ranking algorithm using synthetic data.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest):
    return {"items": recommend_demo(request)}
