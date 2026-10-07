# EvidenceAtlas Food

A local food and nutrition literature search and study-comparison project for CSD358 Track T6. It combines lexical, section-aware, semantic and hybrid retrieval with inspectable source passages.

## Open the application

Double-click **Open EvidenceAtlas.cmd** in this app folder or in its parent EvidenceAtlasFood folder. The interface opens at http://127.0.0.1:8765. Python must be available; this installation uses the existing Anaconda environment.

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
python -m evidenceatlas.cli serve --port 8765
```

Run from this app folder. Requirements are recorded in requirements.txt and requirements-models.txt. See [setup and reproduction instructions](docs/SETUP_REFERENCE.md) for a clean installation, acquisition, model setup and evaluation commands.

## First installation (Windows / PowerShell)

Download and extract this repository, then open PowerShell in its source folder. Python 3.13 was used for development. Suggested layout: source in E:\EvidenceAtlasFood\app, bulk resources in E:\EvidenceAtlasFood.

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
New-Item -ItemType Directory -Force "$env:EAF_ROOT\cache\pip", "$env:EAF_ROOT\tmp" | Out-Null
$env:PIP_CACHE_DIR = "$env:EAF_ROOT\cache\pip"
$env:TEMP = "$env:EAF_ROOT\tmp"
$env:TMP = $env:TEMP
python -m venv "$env:EAF_ROOT\.venv"
$py = "$env:EAF_ROOT\.venv\Scripts\python.exe"
& $py -m pip install -r requirements.txt -r requirements-models.txt
```

If your existing data root already contains the corpus, indexes and models, skip acquisition and encoding. On a fresh data root, download papers and build the indexes:

```powershell
& $py -m evidenceatlas.cli ingest --pages 1 --page-size 25
& $py -m evidenceatlas.cli index
& $py -m evidenceatlas.models embedding reranker
& $py -m evidenceatlas.cli dense-index
```

Start the server:

```powershell
& $py -m evidenceatlas.cli serve --port 8765
```

Open **http://127.0.0.1:8765/**. Stop with Ctrl+C. Opening web/index.html directly does not start the API. For the optional research stance diagnostic, also run `& $py -m evidenceatlas.models nli`.

Acquisition and model downloads require internet access and take time. Source archives contain neither papers nor models. The acquisition command is an initial batch, not a corpus-size limit. Repeating ingestion resumes discovery; use `--pages 0 --seconds 1800` for a larger time-budgeted run, then rebuild the indexes. The storage guard reserves 40 GB free by default. Newly downloaded corpora differ from the frozen evaluation collection. For a custom Python environment, use the explicit serve command above rather than the convenience launcher.

## Reproduce the report evaluation

```powershell
python scripts/evaluate_report.py
```

The report evaluates Precision@3, @5 and @10 using saved top-ten rankings and AI relevance judgments in evaluation/report-v2/. Twelve searches were saved: six original questions, four rewrites and two matched BM25 baselines. Ten runs (100 result positions; 79 unique topic-paper pairs) were graded. The two remaining rewrites are marked screened-only and have no claimed precision scores.

Five presentation examples were selected after inspection; their mean P@3, P@5 and P@10 is 86.7%, 80.0% and 76.0%. The report also gives the original six-question averages and baseline comparison. Selection is disclosed: this is an exploratory demonstration, not a held-out benchmark, independent human gold, or scientific truth score.

The older ten-question, six-method audit is retained under evaluation/everyday-10/ and can still be reproduced with `python scripts/evaluate_everyday.py`. Its labels and top-three scores belong to that separate audit.

To rebuild the PDF, install `reportlab==4.4.9` in a development environment and run `python scripts/build_report.py`. The checked-in report uses the website palette, local Georgia/Segoe UI fonts when available, and bundled PDF fonts otherwise. The existing PDF is included; ReportLab is not needed to run the application.

## Repository layout

| Folder | Contents |
|---|---|
| evidenceatlas/ | Python retrieval, ingestion and local API |
| web/ | HTML/CSS and TypeScript interface; compiled JavaScript included |
| scripts/ | Launch, source packaging and report utilities |
| tests/ | Retrieval and interface checks |
| evaluation/ | Protocols, query sets, saved runs and review materials |
| docs/ | Project documents, course report and demo script |
| docs/checks/ | Measured development and verification results |
| docs/screenshots/ | Interface screenshots |

Only this **app** directory belongs in the GitHub repository. The parent directory holds data/, indexes/, models/, cache/, experiments/ and tmp/. These local resources are required by different runtime or reproduction workflows and are excluded from the source repository. Keep the data root on E:; do not commit private saved investigations.

## Current scope

The frozen collection contains 973 records, 950 searchable papers, 494 full texts and 37,975 section passages. The complete passage embedding index is active. Full text and abstract-only sources are explicitly distinguished.

This is an evidence-retrieval and comparison prototype. Study context is extracted provisionally; automated stance and claim assessment are not independently validated. Small AI-assisted audits are diagnostics, not independent human accuracy benchmarks. See [status](docs/STATUS.md), [open issues](docs/OPEN_ISSUES.md) and [evaluation protocol](evaluation/PROTOCOL.md).

## Course materials

- [Report](docs/EvidenceAtlas_Food_Report.pdf) and [demo script](docs/DEMO_SCRIPT.md)
- [Course requirements](docs/COURSE_REQUIREMENTS.md)
- [Original specification](docs/SPECIFICATION.md) and [agreed reduced scope](docs/DELIVERY_SCOPE.md)

Before submission, add actual team attribution and record the required demo; see docs/COURSE_REQUIREMENTS.md. Implementation and initial documentation used Codex/AI assistance.

## Verify and package

```powershell
python -m pytest tests/test_core.py tests/test_dense.py -q
python scripts/package_source.py
```

API/browser checks require the server and their documented dependencies. Packaging creates releases/EvidenceAtlasFood-source.zip, excludes bulk data and private sessions, and verifies archive hashes.
