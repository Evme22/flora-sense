from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

FILE = Path("bouquets_with_dominant_colors.xlsx")


def parse_list_field(value: Any) -> List[str]:
    if pd.isna(value):
        return []
    return [item.strip().lower() for item in str(value).split(",") if item.strip()]


def normalize_scalar(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def normalize_user_list(values: List[str]) -> List[str]:
    return [normalize_scalar(item) for item in values if normalize_scalar(item)]


def flower_bonus_score(user_flowers: List[str], bouquet_flowers: List[str]) -> float:
    """
    Любимые цветы пользователя трактуются как мягкое пожелание, а не жёсткое требование.

    1.0  -> если совпало 2 и более любимых цветка
    0.6  -> если совпал хотя бы 1 любимый цветок
    0.0  -> если совпадений нет
    """
    if not user_flowers or not bouquet_flowers:
        return 0.0

    user_set = set(item.strip().lower() for item in user_flowers if item.strip())
    bouquet_set = set(item.strip().lower() for item in bouquet_flowers if item.strip())

    matches = len(user_set & bouquet_set)

    if matches >= 2:
        return 1.0
    if matches == 1:
        return 0.6
    return 0.0


def gender_score(user_gender: str, bouquet_gender: str) -> float:
    user_gender = normalize_scalar(user_gender)
    bouquet_gender = normalize_scalar(bouquet_gender)

    if bouquet_gender == user_gender:
        return 1.0
    if bouquet_gender == "universal":
        return 0.7
    return 0.0


def age_score(user_age: str, bouquet_age: str) -> float:
    user_age = normalize_scalar(user_age)
    bouquet_age = normalize_scalar(bouquet_age)

    if bouquet_age == user_age:
        return 1.0
    if bouquet_age == "universal":
        return 0.7
    return 0.0


def occasion_score(user_occasion: str, bouquet_occasion: str) -> float:
    return 1.0 if normalize_scalar(user_occasion) == normalize_scalar(bouquet_occasion) else 0.0


def style_score(user_style: str, bouquet_style: str) -> float:
    normalized_user_style = normalize_scalar(user_style)
    normalized_bouquet_style = normalize_scalar(bouquet_style)

    if not normalized_user_style:
        return 0.0

    return 1.0 if normalized_user_style == normalized_bouquet_style else 0.0


def dominant_color_score(
    user_colors: List[str],
    primary_color: str,
    secondary_color: str,
    bouquet_colors: List[str],
) -> float:
    """
    Основной цвет важнее вторичного, вторичный важнее общей палитры.
    """
    user_set = set(c.strip().lower() for c in user_colors if c.strip())
    if not user_set:
        return 0.0

    primary = normalize_scalar(primary_color)
    secondary = normalize_scalar(secondary_color)
    bouquet_set = set(c.strip().lower() for c in bouquet_colors if c.strip())

    s_primary = 1.0 if primary in user_set else 0.0
    s_secondary = 1.0 if secondary in user_set else 0.0

    if bouquet_set:
        s_palette = len(user_set & bouquet_set) / len(user_set)
    else:
        s_palette = 0.0

    # Главный и второй цвет должны влиять сильнее общей палитры.
    score = 0.7 * s_primary + 0.23 * s_secondary + 0.07 * s_palette
    return max(0.0, min(1.0, score))


def compute_bouquet_score(
    row: pd.Series,
    user_profile: Dict[str, Any],
    weights: Dict[str, float],
) -> float:
    bouquet_colors = parse_list_field(row["colors"])
    bouquet_flowers = [item.strip().lower() for item in str(row["flowers"]).split(",") if item.strip()]

    user_colors = normalize_user_list(user_profile.get("favorite_colors", []))
    user_flowers = normalize_user_list(user_profile.get("favorite_flowers", []))

    s_occasion = occasion_score(user_profile.get("occasion", ""), row["occasion"])
    s_gender = gender_score(user_profile.get("gender", ""), row["recommended_gender"])
    s_age = age_score(user_profile.get("age_group", ""), row["recommended_age_group"])
    s_style = style_score(user_profile.get("style", ""), row["style"])
    s_colors = dominant_color_score(
        user_colors=user_colors,
        primary_color=row["primary_color"],
        secondary_color=row["secondary_color"],
        bouquet_colors=bouquet_colors,
    )
    s_flowers = flower_bonus_score(user_flowers, bouquet_flowers)

    final_score = (
        weights["occasion"] * s_occasion
        + weights["gender"] * s_gender
        + weights["age"] * s_age
        + weights["style"] * s_style
        + weights["colors"] * s_colors
        + weights["flowers"] * s_flowers
    )

    return final_score


def recommend_bouquets(
    file_path: Path,
    user_profile: Dict[str, Any],
    top_n: int = 10,
) -> pd.DataFrame:
    df = pd.read_excel(file_path)

    weights = {
        # Цветовая гамма — главный ориентир в подборе.
        "colors": 8.4,
        # Состав букета заметно влияет, но не превращается в жёсткий фильтр.
        "flowers": 3.1,
        # Стиль важен, но остаётся мягким предпочтением.
        "style": 1.8,
        # Пол и возраст теперь важнее повода, но всё ещё слабее цвета и состава.
        "gender": 1.2,
        "age": 1.1,
        # Повод учитываем как дополнительный контекст, а не доминирующий фактор.
        "occasion": 0.7,
    }

    unwanted_flowers = set(normalize_user_list(user_profile.get("unwanted_flowers", [])))

    if unwanted_flowers:
        df = df[
            ~df["flowers"].fillna("").apply(
                lambda value: bool(set(parse_list_field(value)) & unwanted_flowers)
            )
        ]

    df["score"] = df.apply(lambda row: compute_bouquet_score(row, user_profile, weights), axis=1)

    if user_profile.get("favorite_colors"):
        df["color_match"] = df.apply(
            lambda row: dominant_color_score(
                user_colors=normalize_user_list(user_profile.get("favorite_colors", [])),
                primary_color=row["primary_color"],
                secondary_color=row["secondary_color"],
                bouquet_colors=parse_list_field(row["colors"]),
            ),
            axis=1
        )
        df = df[df["color_match"] >= 0.25]

    result = (
        df.sort_values(by="score", ascending=False)
        .reset_index(drop=True)
        [["id", "filename", "name", "flowers", "colors", "primary_color", "secondary_color",
          "occasion", "recommended_gender", "recommended_age_group", "style", "description", "score"]]
        .head(top_n)
    )

    return result


if __name__ == "__main__":
    user_profile_example = {
        "gender": "female",
        "age_group": "adult",
        "favorite_colors": ["pink", "white"],
        "favorite_flowers": ["роза", "эустома"],
        "unwanted_flowers": ["лилия"],
        "occasion": "birthday",
        "style": "romantic",
    }

    recommendations = recommend_bouquets(
        file_path=FILE,
        user_profile=user_profile_example,
        top_n=10,
    )

    print("\nТоп рекомендаций:\n")
    print(recommendations.to_string(index=False))
