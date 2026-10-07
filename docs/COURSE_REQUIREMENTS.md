# Course requirements from the supplied eight-page PDF

Read in full on 2026-10-06. Source: `CSD358 Information retrieval.pdf`, supplied by the user.

- Track T6 (page 5): professional-domain search must use document structure, including zones, metadata and positional/Boolean queries where appropriate.
- Rubric (page 7): IR principles 30; novelty 10; working system 20; evaluation metrics 15; track relevance 5; report 10; video 10. Total 100.
- Code: GitHub repository link and README covering setup, run instructions, data sources, working and planned features.
- Demo: 5–8 minute prerecorded live demonstration, unlisted YouTube or Drive; **no slides**. Show problem/track (at most one minute), real end-to-end queries and a limitation, pipeline/code/intermediate scores, evaluation and each member's ownership.
- Report: PDF at most eight pages excluding references/appendix. Required sections: problem/track/research; IR principles and pipeline diagram; beyond IR; novelty versus baselines/tools; evaluation with judged queries and baseline; limitations/next steps. Include actual work division and AI-use declaration.
- AI coding and pretrained models are permitted; disclose all uses. Frontend is appreciated but not separately graded. Local execution is sufficient.
- The PDF says build within a 1.5-day window but its deadline table says only “Days”; no usable absolute deadline or submission form URL is provided. Do not invent them.
- The course accepts partial implementations, but the user's product request explicitly requires more. This project does not use the lower course minimum as completion criteria.

## Course concepts to code/experiment map (updated as implemented)
| Concept | Planned implementation | Verification |
|---|---|---|
| Tokenization/case folding | Unicode term tokenizer; preserve negation/numerals | Unit cases + trace |
| Inverted/positional indexes | SQLite postings with positions | Inspect postings, phrase/Boolean checks |
| TF-IDF/cosine | Explicit log-TF/IDF and length norms | Saved baseline runs |
| BM25/top-k | Posting accumulation + heap | Formula tests + latency |
| Zone/parametric indexes | Section/title weights; metadata filters | Flat versus structure-aware ablation |
| Precision/recall | P@k, judged Recall@k, nDCG | Frozen qrels/run evaluator |
| Freshness/deduplication | Cursor checkpoints; content hashes and identifiers | Resume/idempotence checks |
