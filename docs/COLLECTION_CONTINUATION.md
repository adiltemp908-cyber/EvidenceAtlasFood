# Current continuation resources

The November 4 everyday-diet collection is active; see [coverage and verification](COVERAGE_2026_11_04.md). Eleven new topics are defined in `evidenceatlas/taxonomy.py`, with additional human-context screening in `evidenceatlas/topic_screening.py`. Pass those topic names to `continue_collection.py --topics` and specify an explicit `--cutoff`. After acquisition and before screening/indexing, `collect_everyday_reviews.py --run NAME --cutoff YYYY-MM-DD` can add a complementary review/reference-value pass to the same staging corpus. Inspect scope decisions before publishing. Use a new run name after publication.

The historical expansion below preserves the original workflow and measurements.

# Literature continuation — October 13 collection, activated October 19, 2026

The expanded collection is active in the local application. This pass added 893 records and increased searchable papers from 950 to 1,796. Full-text records increased from 494 to 839; 4 of these were recovered for records that previously had abstracts only. The collection now contains 60,420 section-linked passages.

## What changed

- Added dedicated discovery queries for eggs/cholesterol, protein/muscle, breakfast cereals, yogurt/digestion, fruit juice, red meat/cancer and whole grains. Dairy/bone and meal-timing searches were also continued.
- Used PubMed subject-heading searches and Europe PMC title/abstract searches, with date strata 2000–2009, 2010–2019, 2020–2025 and 2026 through October 13. Discovery follows saved cursors; this is not exhaustive coverage of those periods.
- Applied updated screening to 893 new records. Surgical OATS and poultry-production false matches were kept out of search; records and decision history were preserved. There were 29 changed discovery decisions. This was an AI-assisted rule diagnostic, not independent human validation.
- Rebuilt the positional lexical index and encoded 22,445 new/changed passages. Reused 37,975 vectors only after checking unchanged passage text, model, token limit and source-corpus identity.
- Validated vector shape, finite values and normalization, then published the matching corpus/index pair. Existing saved investigations were retained, and the previous live database and index pointer remain available for rollback.

Acquisition used a 900-second target, finishing in 905.7 seconds including in-flight requests. Lexical indexing took 130.3 seconds; the incremental embedding build took 7563.4 seconds. All bulk artifacts remain on E:. Measured project storage at publication was 6.44 GB, with 255.46 GB free on the volume, against the 160 GB budget and 40 GB reserve.

## Checks and unresolved access

Twenty-six core, dense and incremental-index tests passed. Four live hybrid-plus-reranker searches returned source-linked results after publication. These checks establish operation, not retrieval accuracy. The report's saved rankings, Precision@3/@5/@10 and original corpus snapshot remain historical and unchanged.

There were 1 recorded discovery-batch errors; detailed provider responses are in the local run state. 1 existing-record full-text recovery remained unsuccessful: PMC6658129 returned an HTTP 500 from Europe PMC. It remains labelled abstract-only. Provider access failures and incomplete topic coverage are not evidence that the literature does not exist.

## Continue in another measured batch

Run from the app source folder using the installed Python environment. The current workflow requires an existing live corpus and a complete matching passage-level dense index. Choose a **new run name** after a previous run has reached indexing or publication:

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
python scripts/continue_collection.py --run expansion-next --seconds 900
python scripts/rescreen_growth.py --run expansion-next
python scripts/build_expansion.py --run expansion-next
python scripts/publish_expansion.py --run expansion-next
```

Check each command succeeds before running the next. Acquisition can resume an interrupted, not-yet-indexed run with the same name. Embedding checkpoints allow an interrupted build to resume. The source script currently uses the explicit date ranges above; review them when collecting later publications. No fixed paper-count cap is imposed. Small page batches cycle through topics until the time or storage budget is reached.

Publication briefly restarts the localhost server, preserves saved investigations and validates the matching indexes. Do not edit the live corpus concurrently. A failed publication attempts to restore its saved database and index pointer; inspect `status.json` and the server log before retrying. Do not delete the previous index or rollback snapshot until the new collection has been checked.

Local run state, raw acquisition records, checkpoints and rollback copies are under `E:\EvidenceAtlasFood\experiments\expansion-2026-10-13` and the data/index directories. They are excluded from the GitHub source archive. [Measured summary](checks/collection-expansion.json) contains the compact, non-private results.

## Still open

The new collection needs fresh relevance evaluation. Screening, study-arm attribution, evidence stance and context compatibility are not independently validated. A larger corpus can improve coverage, but does not establish improved precision. The report and earlier evaluations must not be presented as scores for this new corpus.
