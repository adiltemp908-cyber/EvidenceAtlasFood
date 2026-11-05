# November 5 repository and report refresh

The updated eight-page report documents all implemented changes through the November 4 collection and summary updates. It preserves historical evaluation scores and distinguishes them from current functional checks. The release passed 77 focused regression tests, TypeScript no-emit checking and reproduction of historical report metrics. See [report](EvidenceAtlas_Food_Report_2026_11_05.pdf), [change log](CHANGELOG_2026_11_05.md) and [release checks](checks/release-2026-11-05.json).

---

# Current status — November 4 everyday-diet collection activated

**3,493 searchable papers, 1,429 searchable full texts, 115,883 semantic vectors.** Added 141 searchable papers, including 81 full texts and 28 papers about water intake/hydration, across eleven everyday-diet topics. All 19 saved investigations were preserved. Thirty-six functional tests passed; six live searches and 82 exact source passages across 29 papers were verified. The original water question now retrieves human plain-water studies and the daily-water-requirement review in its top five.

This is a coverage expansion, not an independent accuracy evaluation. Some everyday queries still rank tangential studies highly; the reranker algorithm was not changed. See [collection scope and checks](COVERAGE_2026_11_04.md).

---

# November 4 answer applicability and search defaults

Hybrid + relevance reranking is now the opening search default, with capability-aware fallbacks. Summary pipeline v9 checks direct applicability before drafting and during final verification, and abstains when it cannot identify findings that directly answer the question in the selected papers. Related quotations remain inspectable; no claim of worldwide absence of research is made. Older saved answers require regeneration.

Thirty-five focused tests, TypeScript compilation, browser checks and synthetic local-model pipeline checks completed. Applicability remains model-assessed; one verifier diagnostic conflated citation support with relevance while correctly suppressing the indirect answer. See [behavior, checks and limitations](LOCAL_SUMMARIES.md). The corpus is unchanged by this update.

---

# October 24 collection activation

**3,352 searchable papers, 1,348 searchable full texts, 109,628 semantic vectors.** Added 428 searchable papers and 155 searchable full texts; incremental indexing is complete and active. See [coverage and checks](COVERAGE_2026_10_23.md). Summary paper-count controls and full-text section reading remain available. No new accuracy claim is made.

---

# Historical checkpoint — October 21 audit repairs

**2,924 searchable papers; 98,356 semantic vectors.** Four missing papers were added with two available full texts; 98,131 previous vectors were reused. Reranking now considers study abstracts across 30 candidates. Summary source-role, context, uncertainty and absence-claim checks address the observed failures, with reusable section readings and one transient-timeout retry. All 19 saved investigations were preserved.

Sixty-four regression checks and a browser check passed. The same three development questions improved from 20/30 to 27/30 directly relevant results at ten; these are AI-assisted judgments on a targeted repair set, not independent accuracy validation. See [recorded checks](checks/audit-gap-repair.json). The report's original evaluations remain historical.

---

# Historical checkpoint — local paper summaries available

October 21, 2026: the search results now include **Summarize top 10 papers**. Qwen3-4B-Instruct-2507 runs locally on the RTX 4050, processes all stored passages, and produces excerpt-grounded answers with inspectable citations. Abstract-only evidence is labelled separately. Functional tests and a ten-paper live/browser check are recorded in [local summary details](LOCAL_SUMMARIES.md). This does not establish independently measured scientific accuracy. No new corpus ingestion or embedding was required for this feature.

---

# Historical checkpoint — semantic passage splitting active

2,920 searchable papers; 86,903 unchanged source passages; 98,131 token-bounded semantic chunks. 79,903 existing vectors reused and 18,228 new vectors encoded. No truncated embedding inputs. [Details and verification](SEMANTIC_CHUNKING.md). Retrieval accuracy has not been independently remeasured.

---

# Historical checkpoint — October 20 food coverage expansion

**2,920 searchable papers, 1,191 searchable full texts, 86,903 indexed passages.** Acquisition and incremental encoding are complete. The optional recency bonus remains active. See [latest coverage](COVERAGE_2026_10_20.md) for measurements and limitations. Current accuracy has not been remeasured; earlier checkpoints follow.

---

# Historical checkpoint — product expansion and recency ranking

The live collection has **2,291 searchable papers, 1,000 searchable full texts and 73,347 indexed passages**. The product batch and incremental encoding are complete. A small, optional recency bonus is active in interactive search. See [product expansion](PRODUCT_EXPANSION.md) for measurements, checks and ranking details.

Thirty-two focused tests and browser checks passed; current precision is not yet evaluated. Previous report scores are historical. The notes below preserve earlier checkpoints.

---

# Historical checkpoint — first expansion activated October 19, 2026

The local application now has **1,866 records, 1,796 searchable papers, 839 full-text records and 60,420 indexed passages**. Lexical and passage-level dense indexes match the active corpus. 22,445 vectors were encoded and 37,975 reused after exact-text/model checks. Acquisition and indexing have finished for this bounded run.

See [collection continuation](COLLECTION_CONTINUATION.md) for measured storage, source-access failures, commands and limitations. Twenty-six tests and four live search checks passed. New accuracy has not been measured; the report and saved evaluations remain tied to their earlier corpus. Context matching and independent scientific validation remain open.

The notes below describe earlier checkpoints and their historical counts; they are retained for provenance.

---

# Historical checkpoint — initial full-text embedding continuation

The user authorized completing full-text embeddings after the reduced delivery. **All 37,975 passage vectors are complete, validated and active.** No encoding or acquisition job is running. The original full specification still has outstanding scientific-validation and context-matching work.

## Implemented and verified
- 973 records, 950 searchable papers, 494 full texts, 473 abstract-only records, six metadata-only records; real acquisition, provenance, screening history, section/table parsing and lexical postings.
- Full-text section-aware BM25, flat TF-IDF/BM25, Boolean/phrase constraints, metadata filters, paper-level semantic baseline and active passage-level semantic/hybrid/reranking.
- Resumed 12,288 existing vectors and encoded 25,687 more in 805.08 seconds, excluding earlier work. All vectors passed shape, finite-value and unit-norm checks; corpus identity stayed unchanged.
- 2,723 passages (7.17%) exceed the 256-token embedding limit. Complete paragraphs remain in lexical search and source inspection. Vectors occupy 58.33 MB. The paper index remains available for validated rollback.
- Source-grounded audience views, comparisons, local saved notes/history, exports and experimental passage NLI/alternative-finding diagnostics remain working.
- 24 core/API tests and 11 browser checks passed; semantic/hybrid/reranking integration returned unique filtered papers with exact matching source text. These are functional checks, not scientific validation.
- The same eight development questions and seven configurations were rerun in passage-v1. All lexical top-10 rankings stayed unchanged; semantic/hybrid rankings changed. Rank change does not establish improvement.
- Report updated to eight pages (seven main pages plus references). Source package, demo guide and reproducibility instructions updated.

## Scientific limitations remain
The historical AI audit belongs to the original paper-index run: 8/12 direct or near-direct relevant results, 2/12 judged directly applicable, both review discussions. The app labels it historical when the passage index is active. Newly retrieved papers do not inherit old judgments. Independent human labels, stance/context accuracy and overall scientific certainty remain unavailable.

Context matching is deferred at the user's request; see OPEN_ISSUES.md. Candidate mentions may refer to background or another arm. Compatibility remains unknown, no automatic claim verdict is inferred, and source relevance is never treated as proof. Reviews/shared cohorts, incomplete status checks and provisional domain screening remain limitations.

## Resources and operation
Bulk footprint at latest inventory: 4.07 decimal GB; E: free 257.94 GB. Budget 160 GB, reserve 40 GB. CPU-only inference. Run run.ps1 and open http://127.0.0.1:8765; model files and literature remain under E:/EvidenceAtlasFood.

Use `python -m evidenceatlas.cli dense-activate --level paper` to restore the baseline, or `--level passage` for the completed full-text index. Switching checks array integrity. The server notices a changed index on its next semantic query; reload the page to refresh its labels.

## Remaining work
Context matching and validated study-arm attribution; independent screening/relevance/stance/context judgments; broader held-out effectiveness and comprehension evaluation; actual team attribution, repository publication, demo recording and course submission. Further corpus expansion, model tuning, exhaustive ablations, complete refresh and public deployment remain deferred. No expert review, video or publication has been invented.

Evidence: passage-index.json, passage-comparison.json, passage-integration.json, browser-check.json, evaluation/passage-v1/, and the preserved evaluation/delivery/ baseline. Corpus fingerprint: eb8022c2e62857317677b2b1b7fb42f40c62777435a0ddada3b3ca6d565534df.

## Interface redesign
The interface now uses phthalo green (#123524), an ivory canvas, desktop navigation rail, responsive mobile navigation, live collection counts, clearer search controls and updated source/compare/evaluation surfaces. Existing workflows passed all 11 browser checks with no JavaScript errors; landing layouts were also checked at 1440, 1280, 768 and 390 px. Open EvidenceAtlas.cmd provides a local browser launcher. The redesign does not change retrieval rankings or scientific-validation status.
