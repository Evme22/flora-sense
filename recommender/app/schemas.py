"""Public demo request and response types based on the private application schema."""
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    gender: str
    age_group: str
    favorite_colors: list[str] = Field(default_factory=list)
    favorite_flowers: list[str] = Field(default_factory=list)
    unwanted_flowers: list[str] = Field(default_factory=list)
    occasion: str
    style: str | None = None
    top_n: int = Field(default=5, ge=1, le=30)


class RecommendationItem(BaseModel):
    id: int | str
    name: str
    flowers: str
    colors: str
    primary_color: str
    secondary_color: str
    occasion: str
    recommended_gender: str
    recommended_age_group: str
    style: str
    description: str
    score: float


class RecommendationResponse(BaseModel):
    items: list[RecommendationItem]
