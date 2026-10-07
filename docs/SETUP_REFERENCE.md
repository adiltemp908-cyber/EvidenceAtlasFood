# EvidenceAtlas Food

A local, source-grounded food/nutrition literature investigation system for CSD358 Track T6. This reduced-scope delivery includes 973 records, 950 searchable papers and 494 full texts; see `docs/DELIVERY_SCOPE.md` and `docs/STATUS.md` for verified functionality and deferred requirements. It is **not yet a validated fact-checking system**.

## Open the interface

Open **http://127.0.0.1:8765** while the local server is running, or double-click **Open EvidenceAtlas.cmd** in this project folder. The launcher opens your browser and starts the local server when needed. It uses the existing Python environment and writes startup logs to E:/EvidenceAtlasFood/tmp/interface-launch.log.

The interface source is in `web/index.html`, `web/styles.css` and `web/app.ts` (compiled to `app.js`). E:/EvidenceAtlasFood holds the literature, models and indexes. Opening index.html directly is not sufficient because the interface uses the local API.

The phthalo-green theme uses #123524, ivory surfaces and responsive layouts. Live collection statistics, source inspection, comparisons, saved investigations and evaluation use the existing backend. Screenshots: docs/screenshots/interface-desktop.png and docs/screenshots/interface-mobile.png.

## Run

Python 3.13 was used on Windows. Dependencies are pinned in `requirements.txt`; the inspected Anaconda environment already contained them. For a clean environment, place the environment/cache on the data volume:

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
$env:PIP_CACHE_DIR = "$env:EAF_ROOT\cache\pip"
$env:TEMP = "$env:EAF_ROOT\tmp"
$env:TMP = $env:TEMP
python -m venv "$env:EAF_ROOT\.venv"
& "$env:EAF_ROOT\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& "$env:EAF_ROOT\.venv\Scripts\python.exe" -m evidenceatlas.cli serve --port 8765
```

With the current environment, simply run `python -m evidenceatlas.cli serve --port 8765` from this project folder and open http://127.0.0.1:8765. The server binds only to localhost. It does not publish queries or notes. No API keys or paid services are used.

## Acquire, index and inspect

```powershell
python -m evidenceatlas.cli ingest --topics caffeine_sleep protein_kidney sodium_pressure meal_timing --pages 1 --page-size 10
python -m evidenceatlas.cli search 'caffeine sleep dose timing' --method structure
python -m evidenceatlas.cli inventory
python -m evidenceatlas.cli ingest --pages 0 --page-size 25 --seconds 1800
python -m evidenceatlas.cli ingest --since 2010-01-01 --until 2019-12-31 --pages 1 --page-size 25
python -m evidenceatlas.cli ingest --refresh --pages 1 --page-size 25
```

`--pages 0` means no paper/page cap; the run stops at the wall-time budget, source exhaustion or storage guard. The wall-time check occurs between pages, so an in-flight page can finish after the deadline. Repeating ingestion resumes each versioned query cursor. `--refresh` starts each query at the beginning and rechecks metadata/status/full-text access; it does not yet guarantee a full-corpus refresh. Dates are query-scope parameters. PubMed ESearch currently stops with an explicit error before its 9,999-ID boundary; use narrower date partitions. Europe PMC uses cursor pagination.

The default growth budget is 160 decimal GB, with 40 GB free space reserved. Override using `EAF_BUDGET_BYTES` and `EAF_RESERVE_BYTES` if needed. Bulk storage on C: is refused. No silent fallback. Data volume paths are configurable on other systems. Raw data, SQLite postings, models, caches, experiments and temporary files all count against the budget.

`probe` runs a deliberately transient in-memory feasibility batch and writes only an explicitly requested measurement report. It is not the normal ingestion path and is not a persistent product corpus.

## Inspectable IR

`retrieval.py` builds an explicit SQLite dictionary/postings index with term frequencies and positions. Flat paper TF-IDF uses `(1+log(tf)) * (log((N+1)/(df+1))+1)` with cosine normalization. BM25 uses k1=1.2, b=.75 and positive Robertson IDF. Structure-aware retrieval ranks section passages with explicit provisional weights, then selects unique parent papers. Relevance is never converted to a truth score. Quoted phrases use positions. Uppercase AND/OR/NOT use an explicit parser; AND binds tighter than OR, adjacent advanced terms imply AND. Plain-language queries use additive term matching. Numerals, units and negation are retained.

Section, year, full-text and human-MeSH filters affect results. Human filtering can miss unindexed studies. Search traces preserve original/expanded query, terms, candidate counts, term contributions, parameters and corpus fingerprint. Source IDs and normalized text offsets support inspection. References are excluded from evidence passages; source background/review claims still require attribution review.

## Optional experimental models

```powershell
python -m pip install -r requirements-models.txt
python -m evidenceatlas.models embedding reranker nli
python -m evidenceatlas.cli dense-index
```

Model revisions are pinned in `models.py`; downloads/cache stay on E:. Models use CPU: four threads for embedding and two for cross-encoders. The active semantic index has 37,975 section-passage vectors, capped at 256 model tokens (2,723 inputs truncated). Complete full-text paragraphs remain searchable through the lexical index. The earlier 950-vector title/abstract index is retained for comparison and rollback. Dense vectors are float32/memory-mapped. Truncation counts are reported. Model similarity, relevance reranking and NLI stance are distinct; none is validated scientific certainty. See status for which model workflows have actually run.

## Evaluation

```powershell
python -m pytest tests/test_core.py -q
python -m evidenceatlas.benchmark claims
python -m evidenceatlas.benchmark freeze --name development-v1
python -m evidenceatlas.benchmark run --name development-v1 --dense
```

The benchmark defines 32 provisional food questions/claims with family-separated development and held-out splits. Freeze first; pool real runs; collect independent judgments using `evaluation/ANNOTATION_GUIDE.md`. Effectiveness metrics remain unavailable until judgments exist. Tests and model smoke checks do not establish food-domain performance. Benchmark snapshots remove private saved sessions.

Browser verification: install Playwright on E: (`pip install --target E:\EvidenceAtlasFood\cache\python-tools playwright==1.55.0`), set `PYTHONPATH` to that directory and run `python tests/browser_check.py` with the server running. It uses an existing Chrome installation and performs search, source, comparison, saving, export and mobile checks. `tests/test_api.py` also requires a running server.

## Data and scientific limits

PubMed MeSH ESearch and Europe PMC title/abstract searches discover records. Metadata screening is versioned but provisional. Only records flagged OA are requested through fullTextXML; article license statements are retained. Some records have no accessible full text. This is not comprehensive coverage, and source counts are not evidence votes. Corrections/status coverage and overlapping cohorts are unresolved unless explicitly documented.

Candidate dose/context mentions link to exact spans; a mention can describe another study or arm. Automated extraction is not silently presented as verified study characteristics. Independent annotation, scientific context validation and calibrated claim assessment remain necessary.

## Ownership and course delivery

This implementation and initial documentation were produced with Codex/AI assistance in this session. The user supplied the product specification and course PDF. Team membership, component ownership, independent reviews and demo recording have not been provided and must not be invented. Course requirements and the exact rubric are recorded in `docs/COURSE_REQUIREMENTS.md`. No GitHub publication, report submission or video recording is claimed.

## Frontend and delivery artifacts

`web/app.ts` is the editable source; `web/app.js` is its checked-in compiled output. Type-check and rebuild with `node E:\EvidenceAtlasFood\cache\typescript\package\lib\tsc.js --project tsconfig.json` (TypeScript 5.9.3). The application runs from the compiled files without Node.

The frozen delivery experiment is `E:\EvidenceAtlasFood\experiments\delivery-v1`; its corpus excludes saved notes. Lightweight run summaries, a review packet, report and demo script are included under `evaluation/` and `docs/`. To use model retrieval in a clean environment, install `requirements-models.txt` inside the E: virtual environment as well. Bulk corpora/model files are not bundled with the source code.

## Resume and verify the AI audit

Context matching remains deferred by the user; see `docs/OPEN_ISSUES.md`. The Collection & evaluation page now shows the small AI audit separately from human-reviewed metrics. Recalculate every label and exact source offset against the frozen corpus without downloading papers or loading models:

```powershell
python -m evidenceatlas.audit E:\EvidenceAtlasFood\experiments\delivery-v1 --output evaluation/delivery/ai-audit-summary.json
```

This checks the predeclared 12-pair sample and rejects missing labels, altered quotes or human labels mixed into the AI audit. It reproduces provisional relevance, not a scientific truth score. `evaluation/AI_AUDIT.md` records the limits.

## Source package and submission

Run `python scripts/package_source.py` to create `releases/EvidenceAtlasFood-source.zip`, with file hashes and archive integrity verification. It includes source, compiled frontend, tests, report and evaluation artifacts. E: corpora/models/caches, private investigations, `.git` and local `.env` are excluded. This is a source delivery, not a standalone bundle of the literature and models; keep the E: directory for this installation or use the acquisition/setup instructions on another machine.

A local Git repository is initialized. Review files before publishing to your chosen repository; no remote URL or public deployment has been configured. Team attribution, reviewed scientific evaluation, demo recording and submission remain genuine user/team work. The PDF now includes the limited AI audit with its limitations.

## Completed full-text embeddings

Full-text passage encoding is complete and active. The original paper-index benchmark/audit remains under `evaluation/delivery/`; the same queries rerun with passage embeddings are under `evaluation/passage-v1/`. The old AI audit is not an accuracy score for newly retrieved results. See `docs/EMBEDDING_RUN.md`, `docs/checks/passage-comparison.json` and `docs/OPEN_ISSUES.md`.

```powershell
python -m evidenceatlas.cli dense-activate --level passage
# Optional rollback, with integrity checks:
python -m evidenceatlas.cli dense-activate --level paper
# Return to the completed full-text index:
python -m evidenceatlas.cli dense-activate --level passage
python -m evidenceatlas.compare_runs E:\EvidenceAtlasFood\experiments\delivery-v1 E:\EvidenceAtlasFood\experiments\passage-v1 evaluation/delivery/ai-judgments.jsonl --output docs/checks/passage-comparison.json
```

The server reloads a switched semantic index on its next model query; refresh the page for its current index label. To verify the completed passage configuration: `python -m pytest tests/test_core.py tests/test_dense.py tests/test_api.py -q`, then `python tests/passage_integration.py` with the server running. `test_dense.py` requires the model dependency set; its tests do not load models or download data.
