# Offline learning-to-rank experiment

**English** | [Русский](ml-experiments.ru.md)

**Run:** May 17, 2026  
**Model:** CatBoostRanker (`YetiRankPairwise`)  
**Deployment status:** Offline experiment only; not used for live ordering

## Objective

Assess whether a supervised ranking model trained on recommendation feedback could outperform the production content-based scoring baseline.

## Signals and labels

The original pipeline grouped impressions by recommendation session and assigned relevance labels from explicit feedback:

| Label | Event |
| ---: | --- |
| 0 | Dislike |
| 1 | Like |
| 2 | Discussion with florist |
| 3 | Custom request created |

Only 0/1 labels actually occurred in the measured run. An impression without a terminal reaction was not treated as a dislike, and rows without explicit feedback were excluded from the target. This prevents conflating a non-response with negative feedback, but limits the size and representativeness of the dataset.

## Data split and results

The source run's metadata reported **140 candidate impressions**, of which **110 had no explicit terminal action**. The remaining **30 labeled rows** belonged to **3 recommendation sessions**. The split was performed at the session level: **2 sessions to train**, **1 to validate**, to avoid placing the same session on both sides.

| Metric | Baseline | CatBoostRanker |
| --- | ---: | ---: |
| NDCG@5 | 0.660840 | 0.514771 |
| NDCG@10 | 0.804581 | 0.776201 |
| Hit rate@5 | 1.000000 | 1.000000 |
| MRR@10 | 0.500000 | 0.500000 |

**Interpretation:** CatBoostRanker did not beat the baseline in this run. Because validation covered only **one session**, the observed difference is not a stable performance estimate or evidence that a learned model would underperform at larger scale. The content-based baseline remained in user-facing operation.

## Features

The training pipeline included bouquet attributes, quiz context, overlap/matching features, baseline rank/position, and session/batch information. Data were grouped by recommendation session for the ranking objective.

## Reproducibility boundary

The [metric implementations](../recommender/training/metrics.py) and their unit tests are public. The client-related dataset, complete database extraction/train pipeline, and model artifacts are kept private. These published metrics were copied from the experiment's recorded metadata, **not recomputed from the synthetic demo catalog**. Accordingly, this repository demonstrates the ranking service and calculation methods, but cannot independently reproduce the original model training result.
