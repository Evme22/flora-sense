# System architecture and public-demo boundaries

## Full application (private)

- **Frontend**: React + Vite; product catalog, shopping flows, quiz, results, admin dashboard.
- **Gateway**: Nginx proxies browser API requests to backend and image requests to the recommendation service.
- **Backend**: Node.js + Express REST API for users, orders, payments, delivery, and recording recommendation sessions/feedback.
- **Persistence**: PostgreSQL with PostGIS delivery-zone polygons and SQL migrations.
- **Recommendation service**: Python + FastAPI. A content-based algorithm loads a bouquet feature catalog from Excel, excludes unwanted flowers, computes feature-based match scores, and returns a sorted list.
- **Session personalization**: The React client applies `sessionReranking.js` after user likes/dislikes to the unshown suffix of the returned list.
- **External integrations**: DaData address suggestions, YooKassa test payments and SMTP email flows, which are not required in this standalone demo.
- **Infrastructure**: Docker Compose orchestration and separate services. The public demo deliberately does not include the application Compose configuration.

## In this repository (public)

- The original scoring and ranking functions in `recommender/prototype/bouquet_recommender_v1.py`.
- A compact FastAPI adapter in `recommender/app` that reads a **synthetic** 12-bouquet dataset. It replaces the private product/image data, not the scoring algorithm.
- The original JS session reranking module in `session-reranking/sessionReranking.js`.
- Ranking metrics from the offline experiment and runnable tests.
- Screenshots and a link to a video walkthrough of the full application.

The public `/recommend` endpoint **does not** apply session feedback reranking. In the actual application the initial recommendation API is called first, and the **frontend JS** adjusts the remaining order after feedback. The two parts are shown separately in the repository to make the division of responsibilities clear.

## Ranking rules and implementation details

The content-based baseline weights color 8.4, flowers 3.1, style 1.8, gender 1.2, age 1.1, and occasion 0.7. Color matching weights primary color 0.70, secondary color 0.23, and palette overlap 0.07.

`unwanted_flowers` is a hard exclusion. A selected color also activates a minimal color-match threshold (`>= 0.25` in the original implementation). A flower in `favorite_flowers` contributes a **soft** preference bonus, not a filter.

Session reranking uses quiz alignment, positive and negative aggregate affinity, direct similarity to reacted items, and original position. The current and previously displayed items are kept in place. Only remaining recommendations are sorted; high initial scores can still outweigh feedback adjustments.

## What is intentionally excluded

The private production catalog, customer accounts and interactions, administrator routes, internal order/payment code, image assets from the shop, database backups, training records, model binaries, deployment configuration and secrets are not part of this publication.
