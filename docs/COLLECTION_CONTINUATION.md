# Current continuation resources

The November 4 everyday-diet collection is active; see [coverage and verification](COVERAGE_2026_11_04.md). Eleven new topics are defined in `evidenceatlas/taxonomy.py`, with additional human-context screening in `evidenceatlas/topic_screening.py`. Pass those topic names to `continue_collection.py --topics` and specify an explicit `--cutoff`. After acquisition and before screening/indexing, `collect_everyday_reviews.py --run NAME --cutoff YYYY-MM-DD` can add a complementary review/reference-value pass to the same staging corpus. Inspect scope decisions before publishing. Use a new run name after publication.

## Continue in another measured batch

Run from the app source folder using the installed Python environment. The current workflow requires an existing live corpus and a complete matching passage-level dense index. Choose a **new run name** after a previous run has reached indexing or publication:

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
python scripts/continue_collection.py --run expansion-next --seconds 900 --cutoff (Get-Date -Format yyyy-MM-dd)
python scripts/rescreen_growth.py --run expansion-next
python scripts/build_expansion.py --run expansion-next
python scripts/publish_expansion.py --run expansion-next
```

Check each command succeeds before running the next. Acquisition can resume an interrupted, not-yet-indexed run with the same name. Embedding checkpoints allow an interrupted build to resume. The source script partitions discovery by publication date. Set the cutoff for each new batch. No fixed paper-count cap is imposed. Small page batches cycle through topics until the time or storage budget is reached.

Publication briefly restarts the localhost server, preserves saved investigations and validates the matching indexes. Do not edit the live corpus concurrently. A failed publication attempts to restore its saved database and index pointer; inspect `status.json` and the server log before retrying. Do not delete the previous index or rollback snapshot until the new collection has been checked.

Run state and rollback copies are stored under the data root. Each new batch changes the collection fingerprint. Compare retrieval results using the collection recorded for that evaluation.
