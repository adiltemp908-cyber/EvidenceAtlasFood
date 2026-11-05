# Product coverage and recency preference — October 19, 2026

The product-focused batch is active. It added **526 records** and **183 full-text records**. The live collection now has **2,291 searchable papers**, including **1,000 searchable full texts**, and **73,347 section-linked passages. Stored metadata also includes excluded and pending-review records.

Discovery targeted creatine, plant milks, nuts/seeds, omega-3/fish oil, magnesium, collagen, psyllium, probiotics, sports/energy drinks and whey/protein products. MeSH headings were checked against PubMed; the invalid Sports Drinks heading was replaced with Beverages before acquisition. Title/abstract queries preserved exposure and outcome terms. Available open-access full texts were parsed into sections; unavailable full texts remain labelled abstract-only.

The acquisition target was 600 seconds with small pages cycled across products and date ranges. It was a time budget, not a paper-count cap. 0 batch errors were recorded. Screening held back analytical sensors, traceability, food-processing and drug-delivery titles without a direct clinical focus for review. Domain decisions remain provisional; animal and laboratory papers are not equivalent to human trials.

Incremental indexing reused **60,420** unchanged vectors and encoded **12,927** new/changed passages. Vector integrity and corpus identity were checked before activation. Existing saved investigations and a rollback copy were preserved. Bulk files remain on E:.

## Small recency bonus

Interactive search now slightly prefers newer papers by default. The additive bonus is capped at **3% of the absolute best relevance score in the fetched candidate pool** and halves every five years of publication age. It is applied once, after relevance reranking and before selecting the displayed results. Missing or future years receive no bonus. Scores and the complete formula are exposed in the research trace.

Uncheck **Slightly prefer newer papers** under **Refine search**, or pass `recency=false` to `/api/search`, to use the original relevance ranking. The bonus uses publication year, so papers from the same year receive the same age preference. Recency is a user-requested ranking preference, not a measure of scientific validity. A substantially more relevant older paper can still rank above a recent one.

Thirty-two focused tests passed, including near ties, large relevance gaps, negative reranker scores, missing/future years, disabling the bonus, and avoiding duplicate application. Browser checks confirmed the toggle and mobile layout. Live searches verified source links after activation. These checks do not establish improved accuracy. The report's saved Precision@3/@5/@10 values still belong to its earlier corpus and ranking configuration.

See [measured product coverage](checks/product-expansion.json). Phrase counts diagnose collection gaps; they are not independently judged relevant-study counts. Some product formulations, brands, doses and populations remain sparsely represented.

For another batch, follow [collection continuation](COLLECTION_CONTINUATION.md), choose a new `--run`, and optionally supply `--topics creatine_supplements plant_milks` and `--cutoff YYYY-MM-DD` to the acquisition command. Pass the same run name through screening, indexing and publication. Before resuming an interrupted acquisition, keep its topic list, dates and page size unchanged.
