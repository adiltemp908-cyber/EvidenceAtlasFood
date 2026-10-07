# Current status - full-text embedding continuation completed

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
