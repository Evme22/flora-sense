import test from "node:test";
import assert from "node:assert/strict";
import { rerankRemainingRecommendations, buildSessionPreferenceRepresentation } from "./sessionReranking.js";

const items = [
  { id: 1, name: "Shown", originalPosition: 0, score: 11, flowers: "роза", colors: "pink", primary_color: "pink", secondary_color: "white", occasion: "birthday", style: "romantic", recommended_gender: "female", recommended_age_group: "adult" },
  { id: 2, name: "Blue", originalPosition: 1, score: 10, flowers: "ирис", colors: "blue", primary_color: "blue", secondary_color: "purple", occasion: "birthday", style: "modern", recommended_gender: "universal", recommended_age_group: "adult" },
  { id: 3, name: "Pink", originalPosition: 2, score: 10, flowers: "роза", colors: "pink", primary_color: "pink", secondary_color: "white", occasion: "birthday", style: "romantic", recommended_gender: "female", recommended_age_group: "adult" },
];

test("returns original array without feedback", () => {
  const result = rerankRemainingRecommendations({ items, currentIndex: 0, feedbackEntries: [], quizContext: {} });
  assert.equal(result, items);
});

test("preserves previously shown prefix and candidate set", () => {
  const result = rerankRemainingRecommendations({ items, currentIndex: 0, feedbackEntries: [{ ...items[0], decision: "like" }], quizContext: { favorite_colors: ["pink"] } });
  assert.equal(result[0], items[0]);
  assert.deepEqual(result.map(x => x.id).sort(), items.map(x => x.id).sort());
});

test("likes favor a similar bouquet among remaining items", () => {
  const result = rerankRemainingRecommendations({ items, currentIndex: 0, feedbackEntries: [{ ...items[0], decision: "like" }], quizContext: { favorite_colors: ["pink"], style: "romantic", favorite_flowers: ["роза"] } });
  assert.deepEqual(result.map(x => x.id), [1, 3, 2]);
});

test("does not mutate the original array order", () => {
  const before = items.map(x => x.id);
  rerankRemainingRecommendations({ items, currentIndex: 0, feedbackEntries: [{ ...items[0], decision: "like" }], quizContext: {} });
  assert.deepEqual(items.map(x => x.id), before);
});

test("aggregates likes and dislikes separately", () => {
  const value = buildSessionPreferenceRepresentation([{ ...items[0], decision: "like" }, { ...items[1], decision: "dislike" }]);
  assert.equal(value.likedAggregate.count, 1);
  assert.equal(value.dislikedAggregate.count, 1);
  assert.equal(value.totalFeedback, 2);
});
