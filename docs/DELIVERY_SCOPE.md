# Revised delivery scope — 2026-10-07

The user authorized scaling down to reduce Codex usage, with a stated ceiling of roughly three five-hour usage windows. Account usage cannot be measured from this workspace; do not promise an exact quota. Prefer bounded local jobs and compact verification.

## Finish for this delivery
- Retain the existing 973-record collection (950 searchable papers, 494 ingested full texts), parser v2, provenance and resumable acquisition.
- Keep full-text section-aware lexical retrieval, flat TF-IDF/BM25, Boolean/phrase search and source inspection.
- Complete **paper-level title/abstract dense retrieval** for all searchable papers, hybrid fusion and bounded reranking. This cuts encoding from 37,975 passages to 950 papers. Full-text dense passage encoding is deferred; retain its 12,288-vector checkpoint.
- Verify public, dietitian and research investigation workflows, comparisons, persistent notes, citations and exports.
- Provide conservative source-grounded research observations, explicit unknown context, and separately marked experimental stance analysis. Do not market unvalidated model output as a reliable fact-check verdict.
- Run a bounded frozen development experiment and publish real runtime/ranking artifacts. Supply a small review packet and validated judgment import/evaluation workflow. Human effectiveness metrics remain unavailable until real reviewers contribute.
- Deliver setup instructions, current status, a course-aligned report and a live-demo script. No video, team attribution or expert review is fabricated.

## Deferred by this scope change
Further corpus expansion; full-text dense vectors; model training/tuning; exhaustive ablations; validated automatic PICO/arm attribution and certainty synthesis; expert/user studies; automated full-corpus refresh; public deployment. These remain roadmap items, not fulfilled requirements of the original specification.

Scientific integrity, real full-text ingestion, inspectable IR and honest reproducibility are retained. The original specification remains preserved for reference; this document records the user's subsequent scope authorization.

## Subsequent user authorization: resume embeddings
The user explicitly requested continuing the embedding work. Resume the existing full-text passage checkpoint, validate the complete array before activation, preserve the paper index for rollback, and run a bounded comparison on the existing development questions. No new corpus expansion or paid service is inferred. Other reduced-scope deferrals remain in effect.
