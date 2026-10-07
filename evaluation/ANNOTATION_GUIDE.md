# Blinded review instructions

These queries are claims to investigate, not statements assumed true. The query set was authored with AI assistance. No labels have been assigned by humans.

1. Open the frozen snapshot's `blinded-pool.json` and the article text identified by each passage ID. Record your reviewer ID and actual qualifications; use `reviewer_kind: human` only for your own review. Model or AI-assisted suggestions must be retained separately.
2. Read surrounding methods, results and limitations, not only the highlighted passage. A literature-review statement, study protocol or background citation is not automatically the paper's own observed result.
3. Grade relevance 0–3 using PROTOCOL.md. Assign stance toward the **original claim** separately. Use `insufficient to establish` for related evidence that does not establish or contradict the claim; nonsignificance alone is not proof of no effect.
4. Mark each context field matches/differs/unknown with exact supporting source spans. Check food identity, preparation, dose/units, duration, timing, population/health status, comparator/substitution and outcome. A mismatch can coexist with a supportive passage stance.
5. Copy rationale offsets from the frozen normalized passage; store both offsets and exact quote. The validator rejects mismatched quotes, paper IDs and corpus versions.
6. Flag retractions/corrections, protocols, reviews, unresolved shared cohorts, surrogate outcomes, animal experiments and inaccessible full texts. These characteristics are not universal quality scores.
7. Review independently before comparing labels. Preserve initial judgments, disagreement and adjudication. Dietitian/researcher review is desirable; absence must be disclosed.

Before effectiveness evaluation, pilot these instructions on a small batch and record ambiguous cases. Judged recall is relative to the pool; it is not recall over all literature. Keep labels outside `data/normalized` and never add annotations or gold IDs as inference filters.

The held-out claim families must not be used to tune normalization, weights, context rules, prompts or model choice. Training contamination from pretrained models cannot be ruled out; disclose it.
