function normalizeScalar(value) {
  return String(value || "").trim().toLowerCase();
}

function normalizeListField(value) {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeScalar(item)).filter(Boolean);
  }

  return String(value || "")
    .split(",")
    .map((item) => normalizeScalar(item))
    .filter(Boolean);
}

function normalizeBouquetItem(item) {
  return {
    id: String(item.id),
    originalPosition: Number(item.originalPosition ?? 0),
    score: Number(item.score) || 0,
    flowers: normalizeListField(item.flowers),
    colors: normalizeListField(item.colors),
    primaryColor: normalizeScalar(item.primary_color),
    secondaryColor: normalizeScalar(item.secondary_color),
    occasion: normalizeScalar(item.occasion),
    recommendedGender: normalizeScalar(item.recommended_gender),
    recommendedAgeGroup: normalizeScalar(item.recommended_age_group),
    style: normalizeScalar(item.style),
  };
}

function buildFrequencyMap(items, key) {
  const counts = new Map();

  for (const item of items) {
    const value = item[key];

    if (!value) {
      continue;
    }

    counts.set(value, (counts.get(value) || 0) + 1);
  }

  return counts;
}

function buildTokenFrequencyMap(items, key) {
  const counts = new Map();

  for (const item of items) {
    for (const token of item[key]) {
      counts.set(token, (counts.get(token) || 0) + 1);
    }
  }

  return counts;
}

function buildAggregate(items) {
  return {
    count: items.length,
    primaryColorCounts: buildFrequencyMap(items, "primaryColor"),
    secondaryColorCounts: buildFrequencyMap(items, "secondaryColor"),
    occasionCounts: buildFrequencyMap(items, "occasion"),
    styleCounts: buildFrequencyMap(items, "style"),
    genderCounts: buildFrequencyMap(items, "recommendedGender"),
    ageCounts: buildFrequencyMap(items, "recommendedAgeGroup"),
    flowerCounts: buildTokenFrequencyMap(items, "flowers"),
    colorCounts: buildTokenFrequencyMap(items, "colors"),
  };
}

function matchScalar(token, counts, total) {
  if (!token || !counts.size || total <= 0) {
    return 0;
  }

  return (counts.get(token) || 0) / total;
}

function matchTokenList(tokens, counts, total) {
  if (!tokens.length || !counts.size || total <= 0) {
    return 0;
  }

  const sum = tokens.reduce((acc, token) => acc + (counts.get(token) || 0) / total, 0);
  return sum / tokens.length;
}

function exactOrUniversalMatch(target, candidate) {
  if (!target || !candidate) {
    return 0;
  }

  if (target === candidate) {
    return 1;
  }

  if (candidate === "universal") {
    return 0.65;
  }

  return 0;
}

function setOverlapScore(sourceTokens, candidateTokens) {
  if (!sourceTokens.length || !candidateTokens.length) {
    return 0;
  }

  const sourceSet = new Set(sourceTokens);
  const candidateSet = new Set(candidateTokens);
  let overlap = 0;

  for (const token of candidateSet) {
    if (sourceSet.has(token)) {
      overlap += 1;
    }
  }

  return overlap / Math.max(sourceSet.size, candidateSet.size);
}

function buildQuizPreference(quizContext = {}) {
  return {
    favoriteColors: normalizeListField(quizContext.favorite_colors),
    favoriteFlowers: normalizeListField(quizContext.favorite_flowers),
    occasion: normalizeScalar(quizContext.occasion),
    style: normalizeScalar(quizContext.style),
    gender: normalizeScalar(quizContext.gender),
    ageGroup: normalizeScalar(quizContext.age_group),
  };
}

export function buildSessionPreferenceRepresentation(feedbackEntries, quizContext = {}) {
  const likedItems = feedbackEntries
    .filter((entry) => entry.decision === "like")
    .map((entry) => normalizeBouquetItem(entry));
  const dislikedItems = feedbackEntries
    .filter((entry) => entry.decision === "dislike")
    .map((entry) => normalizeBouquetItem(entry));

  return {
    quizPreference: buildQuizPreference(quizContext),
    likedItems,
    dislikedItems,
    likedAggregate: buildAggregate(likedItems),
    dislikedAggregate: buildAggregate(dislikedItems),
    totalFeedback: feedbackEntries.length,
  };
}

function computeQuizAlignment(candidate, quizPreference) {
  const colorMatch = quizPreference.favoriteColors.length
    ? Math.max(
        quizPreference.favoriteColors.includes(candidate.primaryColor) ? 1 : 0,
        quizPreference.favoriteColors.includes(candidate.secondaryColor) ? 0.7 : 0,
        setOverlapScore(quizPreference.favoriteColors, candidate.colors)
      )
    : 0;

  const flowerMatch = setOverlapScore(quizPreference.favoriteFlowers, candidate.flowers);
  const styleMatch =
    quizPreference.style && candidate.style && quizPreference.style === candidate.style ? 1 : 0;
  const occasionMatch =
    quizPreference.occasion && candidate.occasion && quizPreference.occasion === candidate.occasion
      ? 1
      : 0;
  const genderMatch = exactOrUniversalMatch(quizPreference.gender, candidate.recommendedGender);
  const ageMatch = exactOrUniversalMatch(quizPreference.ageGroup, candidate.recommendedAgeGroup);

  return (
    colorMatch * 0.48 +
    flowerMatch * 0.24 +
    styleMatch * 0.12 +
    occasionMatch * 0.06 +
    genderMatch * 0.06 +
    ageMatch * 0.04
  );
}

function computeAggregateAffinity(candidate, aggregate) {
  if (!aggregate.count) {
    return 0;
  }

  const primaryMatch = matchScalar(candidate.primaryColor, aggregate.primaryColorCounts, aggregate.count);
  const secondaryMatch = matchScalar(
    candidate.secondaryColor,
    aggregate.secondaryColorCounts,
    aggregate.count
  );
  const colorsMatch = matchTokenList(candidate.colors, aggregate.colorCounts, aggregate.count);
  const flowersMatch = matchTokenList(candidate.flowers, aggregate.flowerCounts, aggregate.count);
  const styleMatch = matchScalar(candidate.style, aggregate.styleCounts, aggregate.count);
  const occasionMatch = matchScalar(candidate.occasion, aggregate.occasionCounts, aggregate.count);
  const genderMatch = matchScalar(candidate.recommendedGender, aggregate.genderCounts, aggregate.count);
  const ageMatch = matchScalar(candidate.recommendedAgeGroup, aggregate.ageCounts, aggregate.count);

  return (
    primaryMatch * 0.28 +
    secondaryMatch * 0.16 +
    colorsMatch * 0.18 +
    flowersMatch * 0.18 +
    styleMatch * 0.1 +
    occasionMatch * 0.05 +
    genderMatch * 0.03 +
    ageMatch * 0.02
  );
}

function computeDirectPairAffinity(candidate, reference) {
  const primaryMatch =
    candidate.primaryColor && reference.primaryColor && candidate.primaryColor === reference.primaryColor
      ? 1
      : 0;
  const secondaryMatch =
    candidate.secondaryColor &&
    reference.secondaryColor &&
    candidate.secondaryColor === reference.secondaryColor
      ? 1
      : 0;
  const colorsMatch = setOverlapScore(reference.colors, candidate.colors);
  const flowersMatch = setOverlapScore(reference.flowers, candidate.flowers);
  const styleMatch = candidate.style && reference.style && candidate.style === reference.style ? 1 : 0;
  const occasionMatch = candidate.occasion && reference.occasion && candidate.occasion === reference.occasion ? 1 : 0;
  const genderMatch = exactOrUniversalMatch(reference.recommendedGender, candidate.recommendedGender);
  const ageMatch = exactOrUniversalMatch(
    reference.recommendedAgeGroup,
    candidate.recommendedAgeGroup
  );

  return (
    primaryMatch * 0.26 +
    secondaryMatch * 0.14 +
    colorsMatch * 0.2 +
    flowersMatch * 0.2 +
    styleMatch * 0.1 +
    occasionMatch * 0.05 +
    genderMatch * 0.03 +
    ageMatch * 0.02
  );
}

function computeReferenceAffinity(candidate, references) {
  if (!references.length) {
    return 0;
  }

  const scores = references.map((reference) => computeDirectPairAffinity(candidate, reference));
  const average = scores.reduce((sum, value) => sum + value, 0) / scores.length;
  const strongest = Math.max(...scores);

  return strongest * 0.7 + average * 0.3;
}

function normalizeBaselineScores(items) {
  const values = items.map((item) => Number(item.score) || 0);
  const min = Math.min(...values);
  const max = Math.max(...values);

  return new Map(
    items.map((item) => {
      if (max === min) {
        return [String(item.id), 1];
      }

      return [String(item.id), ((Number(item.score) || 0) - min) / (max - min)];
    })
  );
}

export function rerankRemainingRecommendations({
  items,
  currentIndex,
  feedbackEntries,
  quizContext,
}) {
  if (!Array.isArray(items) || items.length === 0) {
    return items;
  }

  if (!Array.isArray(feedbackEntries) || feedbackEntries.length === 0) {
    return items;
  }

  const boundaryIndex = currentIndex + 1;

  if (boundaryIndex >= items.length) {
    return items;
  }

  const shownPrefix = items.slice(0, boundaryIndex);
  const remaining = items.slice(boundaryIndex);

  if (remaining.length <= 1) {
    return items;
  }

  const representation = buildSessionPreferenceRepresentation(feedbackEntries, quizContext);
  const sessionWeight = Math.min(0.46, 0.18 + (representation.totalFeedback - 1) * 0.08);

  if (sessionWeight <= 0) {
    return items;
  }

  const baselineById = normalizeBaselineScores(remaining);

  const rerankedTail = [...remaining].sort((left, right) => {
    const leftCandidate = normalizeBouquetItem(left);
    const rightCandidate = normalizeBouquetItem(right);

    const leftQuiz = computeQuizAlignment(leftCandidate, representation.quizPreference);
    const rightQuiz = computeQuizAlignment(rightCandidate, representation.quizPreference);

    const leftPositive = computeAggregateAffinity(leftCandidate, representation.likedAggregate);
    const rightPositive = computeAggregateAffinity(rightCandidate, representation.likedAggregate);

    const leftNegative = computeAggregateAffinity(leftCandidate, representation.dislikedAggregate);
    const rightNegative = computeAggregateAffinity(rightCandidate, representation.dislikedAggregate);

    const leftPositiveReference = computeReferenceAffinity(leftCandidate, representation.likedItems);
    const rightPositiveReference = computeReferenceAffinity(rightCandidate, representation.likedItems);

    const leftNegativeReference = computeReferenceAffinity(leftCandidate, representation.dislikedItems);
    const rightNegativeReference = computeReferenceAffinity(rightCandidate, representation.dislikedItems);

    const leftSession =
      leftPositiveReference * 0.62 +
      leftPositive * 0.38 -
      (leftNegativeReference * 0.78 + leftNegative * 0.52);
    const rightSession =
      rightPositiveReference * 0.62 +
      rightPositive * 0.38 -
      (rightNegativeReference * 0.78 + rightNegative * 0.52);

    const leftPrior =
      remaining.length <= 1
        ? 1
        : 1 - leftCandidate.originalPosition / Math.max(1, items.length - 1);
    const rightPrior =
      remaining.length <= 1
        ? 1
        : 1 - rightCandidate.originalPosition / Math.max(1, items.length - 1);

    const leftScore =
      (baselineById.get(String(left.id)) || 0) * 0.48 +
      leftQuiz * 0.26 +
      leftSession * sessionWeight +
      leftPrior * 0.06;
    const rightScore =
      (baselineById.get(String(right.id)) || 0) * 0.48 +
      rightQuiz * 0.26 +
      rightSession * sessionWeight +
      rightPrior * 0.06;

    if (rightScore !== leftScore) {
      return rightScore - leftScore;
    }

    return leftCandidate.originalPosition - rightCandidate.originalPosition;
  });

  return [...shownPrefix, ...rerankedTail];
}
