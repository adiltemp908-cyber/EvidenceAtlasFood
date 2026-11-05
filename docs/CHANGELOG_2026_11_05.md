# Repository update - November 5, 2026

This release brings the published October source up to the current local application. The collection counts below describe the November 4 activation; this release does not acquire new papers or rebuild the live index.

## Included changes

- Collection continuation, provisional topic screening, staged publication and incremental vector reuse across the October and November expansions. Current snapshot: 3,723 records, 3,493 searchable papers, 1,429 searchable full texts and 102,752 source passages.
- Overlapping tokenizer-bounded semantic chunks: 115,883 active vectors and no truncated embedding inputs in the recorded activation. Original passages and exact source offsets remain available.
- Query-focused abstract reranking across up to 30 candidates, vocabulary improvements, and an optional capped recency preference with trace details.
- Local Qwen3 paper summaries with complete stored-section reading, source quotations, context guards, progress, cancellation, transient retry and caches.
- A 1-10 paper selector (default 3), reusable reading plans and section readings, and visible cache information.
- Summary pipeline v9 applicability checks and abstention when selected evidence cannot directly answer the question. Capability-aware Hybrid + relevance reranking defaults.
- Regression tests, collection/check records, targeted development judgments, source setup and updated TypeScript/compiled browser assets.

## Documentation and delivery

- New eight-page November 5 report in PDF and Markdown; standard report links now open current content.
- Original October report and previously published final-report PDFs preserved. Separate historical report builder prevents old report generation from replacing the new report.
- README, document index, status, open issues and demo plan refreshed. Existing published attribution and demo link retained.
- Source packaging now refreshes the root SHA-256 manifest and includes the published root PDF. The source archive verifies every packaged file against the manifest. .gitattributes preserves exact file bytes across platforms, including the original frozen evaluation artifacts, so source hashes remain reproducible.
- Bulk literature, model weights, indexes, private saved investigations and generated summaries remain outside Git and the source package.

## Validation

On November 5, 77 focused regression tests passed. TypeScript no-emit compilation passed. Historical report evaluation was reproduced from saved rankings and labels. PDF pages were rendered and visually reviewed; source package hashes and the extracted delivery copy were verified.

Commands and exact scope are recorded in [release checks](checks/release-2026-11-05.json). The legacy live API test was excluded because it assumes a historical audit matches the expanded corpus and writes a saved investigation. No fresh live-model benchmark or browser run is claimed for this documentation/source release.

Historical precision scores are unchanged. Neither the expanded corpus nor the summary pipeline has an independently judged accuracy benchmark. The report distinguishes recorded development checks from independent scientific validation.
