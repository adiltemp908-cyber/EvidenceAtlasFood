# EvidenceAtlas Food

**Explore the research behind everyday food questions.**

Is cereal a good everyday breakfast? Does eating late at night matter? EvidenceAtlas Food helps readers find relevant nutrition studies, inspect the passages behind a result, and compare what different studies actually examined. It is a local Information Retrieval project for **CSD358, Track T6**, with everyday, dietitian and research views built around the same sources.

![EvidenceAtlas Food interface](docs/screenshots/report-home.png)

[Updated report - November 5](docs/EvidenceAtlas_Food_Report_2026_11_05.pdf) · [Setup](#run-the-project) · [Evaluation](#how-we-evaluated-search) · [Collection status](docs/COLLECTION_CONTINUATION.md)

**Adil Muhammed | Roll No. 2410110018**

[Existing demo video](https://drive.google.com/drive/folders/1J2qyEUmowNZrV7AOvcICCEFa07_YCeAx?usp=drive_link) · [Original published report](EvidenceAtlasFood-Report-Final.pdf) · [November 5 change log](docs/CHANGELOG_2026_11_05.md)

## From a food question to research evidence

### 1. Collect literature about food and nutrition

We used scientific subject headings and title/abstract queries through PubMed and Europe PMC to discover papers across nutrition topics. Records are deduplicated, screened for domain relevance, and stored with identifiers and acquisition history. Screening rules reduce obvious mismatches such as crop-production papers and the surgical acronym “OATS”; they remain provisional rules, not expert validation.

The collection began as a measured pilot and expanded in batches. A later pass recovered missing open-access full texts and added searches for eggs and cholesterol, protein and muscle, breakfast cereals, yogurt, fruit juice, red meat, and whole grains. Searches span several publication periods so that recent papers do not dominate every topic.

A further product-focused batch expanded coverage of creatine, plant milks, nuts/seeds, fish oil, magnesium, collagen, psyllium, probiotics, sports drinks and whey products.

### 2. Keep the passages that make a result inspectable

Available open-access full texts are downloaded as structured XML and separated into section-linked passages. Abstract-only records remain clearly labelled. Titles, abstracts, body sections and available table content can contribute to retrieval, while the reader can inspect the original wording and follow the source identifiers.

| Collection | Records | Searchable papers | Full-text records | Passages |
|---|---:|---:|---:|---:|
| October 7 report snapshot | 973 | 950 | 494 | 37,975 |
| October 13 expanded collection | 1,866 | 1,796 | 839 | 60,420 |
| October 19 product expansion | 2,392 | 2,291 | 1,022 | 73,347 |
| October 20 coverage expansion | 3,054 | 2,920 | 1,213 | 86,903 |
| October 23 coverage expansion | 3,534 | 3,352 | 1,386 | 97,245 |
| November 4 everyday-diet expansion | 3,723 | 3,493 | 1,475 | 102,752 |

The latest targeted batch added 141 searchable papers across eleven everyday-diet topics, including 28 papers on water intake and hydration. See [everyday diet coverage](docs/COVERAGE_2026_11_04.md). These are local collection counts, not a claim of comprehensive nutrition coverage. The report evaluation uses its original frozen snapshot.

### 3. Retrieve by words, meaning, or both

The search engine supports Boolean and phrase search, TF-IDF, BM25 and section-aware lexical ranking. Semantic search uses **all-MiniLM-L6-v2** to turn passages and questions into vectors; hybrid search combines lexical and semantic candidates. Optional relevance ranking uses the **ms-marco-MiniLM-L6-v2 cross-encoder** to score query–passage pairs.

The interface opens with **Hybrid + relevance reranking** selected when both models/indexes are available. Other retrieval methods remain available under **Refine search**.

This makes the IR pipeline inspectable: the research view exposes retrieval details, and results retain their source passages. Semantic inputs have a 256-token limit; complete stored paragraphs remain available for lexical search and reading. The reranker scores selected passages, rather than reading every candidate paper in full.

Expansion now reuses vectors only when the passage ID, complete text, pinned model and token limit match. Newly added or changed passages are encoded separately, with resumable checkpoints.

Interactive search also offers **Slightly prefer newer papers** under **Refine search**. Its capped 3% recency bonus halves every five years and is applied after relevance ranking. Turn it off for relevance-only comparisons; the formula and individual bonuses appear in the research trace. See [product coverage and ranking changes](docs/PRODUCT_EXPANSION.md).

### 4. Read and compare studies in context

The phthalo-green interface provides everyday explanations alongside deeper dietitian and research views. Readers can open sources, compare selected studies, save investigations locally, and export evidence. Population, intervention, dose, timing, comparator and outcomes matter when interpreting a finding; extracted context is provisional and needs checking against the paper.

The application helps readers examine evidence. A relevant search result does not by itself establish that a food claim is true, and automated stance diagnostics are experimental.

### 5. Ask a local model to read the retrieved papers

After a search, set **Papers** to a number from **1–10** (default **3**) and click **Summarize**. A locally hosted **Qwen3-4B-Instruct-2507** model reads every stored passage of those papers in bounded section groups, then writes a short answer with links to exact source quotations. Full-text and abstract-only coverage is shown separately. You can inspect what was read, stop a running summary, and reuse completed summaries.

The model runs on the GPU independently of MiniLM retrieval and reranking. It does not change the search rankings or require new embeddings. Answers are constrained to cited excerpts and checked for unsupported content, but these checks do not guarantee scientific correctness. The result is a reading aid, not an expert review or a systematic review. See [local summary details](docs/LOCAL_SUMMARIES.md).

When the model cannot identify findings that directly answer the question, it says so instead of presenting related findings as an answer. This statement applies to the selected papers and available text; it does not imply that no relevant studies exist elsewhere. Explicit population, dose, timing, comparator and outcome constraints are considered, and direct null results remain eligible.

## Run the project

### Existing local installation

Open PowerShell in the source folder, normally `E:\EvidenceAtlasFood\app`, and use the Python environment with the project dependencies installed:

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
python -m evidenceatlas.cli serve --port 8765
```

Open **http://127.0.0.1:8765/**. Stop the server with **Ctrl+C**. The existing Windows installation also has an **Open EvidenceAtlas.cmd** launcher. Opening `web/index.html` alone does not start the search API.

### Clean installation

Download the repository and open PowerShell in its source folder. Development used Python 3.13 on Windows. Keep source in `E:\EvidenceAtlasFood\app` and bulk resources under `E:\EvidenceAtlasFood`, or choose another writable data volume through `EAF_ROOT`.

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

If the data root already contains the corpus, models and matching indexes, skip the next block. For a fresh installation:

```powershell
& $py -m evidenceatlas.cli ingest --pages 1 --page-size 25
& $py -m evidenceatlas.cli index
& $py -m evidenceatlas.models embedding reranker
& $py -m evidenceatlas.cli dense-index
```

Then start the application:

```powershell
& $py -m evidenceatlas.cli serve --port 8765
```

Downloads require internet access and time. Retrieval models run locally on CPU; the optional summary model uses the GPU. No paid LLM API is required. Compiled browser JavaScript is included, so Node.js is not needed to run the site. Optional stance diagnostics also require `& $py -m evidenceatlas.models nli`.

The source repository contains **neither the paper corpus nor model weights**. Fresh acquisition produces a different collection from the saved report snapshot. The first ingestion command is an initial batch, not a paper-count cap. Further acquisition and incremental indexing are described in [collection continuation](docs/COLLECTION_CONTINUATION.md). Default storage settings budget 160 GB and reserve 40 GB free; these are limits, not download targets.

In a new PowerShell session, set `EAF_ROOT` and `$py` again. For a custom environment, use the explicit serve command rather than relying on the convenience launcher. More configuration details are in [setup reference](docs/SETUP_REFERENCE.md).

### Optional local answer summaries

The current E: installation already includes the model. For a new installation on **Windows x64 with an NVIDIA GPU supporting Vulkan**, run this once after installing the Python dependencies:

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
python scripts/setup_summarizer.py
```

If using the virtual environment created above, replace `python` with `& $py`. The script downloads roughly **2.5 GB** of pinned model weights plus the portable runtime onto `EAF_ROOT`, and verifies their checksums. Keep an up-to-date NVIDIA driver. This configuration was exercised on an RTX 4050 Laptop GPU with **6 GB VRAM** and about **16 GB system RAM**; measured model GPU use was approximately **3.8 GB**.

Start the application normally, run a search, and set **Papers** to a number from **1–10** (default **3**) and click **Summarize**. The model starts automatically; no separate model-server command or paid API key is needed. First readings can take several minutes, depending on paper length. Identical completed requests use a local cache. Changing the paper count reuses matching section readings for the same question; token-bounded preparation plans are reused across questions whenever the source text and tokenizer are unchanged. Choosing fewer papers reduces reading time and evidence coverage. No sections of a chosen paper are silently skipped. **Stop reading** finishes the current section and preserves completed work. The model unloads after 120 seconds idle to release GPU memory.

The runtime listens on `127.0.0.1:8766`. If that port is occupied, set `$env:EAF_SUMMARY_PORT = '8767'` before starting the app. Downloads need internet access; answer generation stays on your computer. Model weights, private authentication material and generated summaries are excluded from the source ZIP. [Troubleshooting and limitations](docs/LOCAL_SUMMARIES.md).

## How we evaluated search

The report measures **Precision@3, Precision@5 and Precision@10**: the fraction of the first 3, 5 or 10 results judged directly relevant (grade 2) to a query. Partially relevant results do not count toward precision. Saved rankings and judgments allow the scores to be reproduced without fetching papers again:

```powershell
python scripts/evaluate_report.py
```

Twelve searches were saved: six original questions, four rewrites and two matched BM25 baselines. Ten runs were graded, covering 100 result positions and 79 unique topic–paper pairs. Two rewrites were screened only and have no precision score.

| Query group | P@3 | P@5 | P@10 |
|---|---:|---:|---:|
| Six original questions | 88.9% | 76.7% | 63.3% |
| Five presentation examples selected after inspection | 86.7% | 80.0% | 76.0% |

Judgments were AI-assisted. The selected examples demonstrate useful searches; they are not an unbiased test set or independent human gold standard. Precision measures relevance, not scientific truth. These results belong to the historical report collection and do **not** measure accuracy on the expanded November collection.

The earlier ten-question, six-method audit remains in `evaluation/everyday-10/`, reproducible with `python scripts/evaluate_everyday.py`. It is a separate diagnostic. Independent relevance judgments, validated study-context matching and broader held-out evaluation remain future work.

## What belongs in the repository

| Location | Purpose |
|---|---|
| `evidenceatlas/` | Acquisition, parsing, retrieval, embeddings and local API |
| `web/` | Interface source and compiled browser files |
| `scripts/` | Collection continuation, launch, evaluation and packaging tools |
| `tests/` | Functional and retrieval regression checks |
| `evaluation/` | Query sets, saved rankings, judgments and protocols |
| `docs/` | Report, screenshots, setup, decisions and measured checks |

Only the **app source folder** belongs in GitHub. Its parent data root holds `data/`, `indexes/`, `models/`, `cache/`, `experiments/` and `tmp/`. Keep downloaded literature, caches, rollback databases and private saved investigations out of the source repository.

## Verification and course deliverables

```powershell
python -m pytest tests/test_core.py tests/test_dense.py tests/test_incremental.py tests/test_recency.py tests/test_chunking.py tests/test_everyday_topics.py tests/test_summarization.py tests/test_summary_evidence.py tests/test_summary_speed.py -q --basetemp "$env:EAF_ROOT/tmp/release-tests"
python scripts/package_source.py
```

Packaging produces `releases/EvidenceAtlasFood-source.zip` and verifies its file hashes. The November 5 report PDF and historical reports are included. The current Markdown source is `docs/REPORT_2026_11_05.md`; `scripts/build_historical_report.py` rebuilds the October report separately. To rebuild the current report, install `reportlab==4.4.9` and run `python scripts/build_report.py`; ReportLab is not needed for the application.

See the [demo script](docs/DEMO_SCRIPT.md), [course requirements](docs/COURSE_REQUIREMENTS.md), [status](docs/STATUS.md) and [open issues](docs/OPEN_ISSUES.md). The published attribution and existing demo link are preserved above; the recording has not been revalidated against this release. Implementation and initial documentation used Codex/AI assistance; expert review and independent benchmark validation have not been claimed.

### Semantic passage coverage

Long passages are split into overlapping, tokenizer-bounded chunks. The current index contains **115,883 semantic vectors** from **102,752 source passages**, with no truncated embedding inputs. This affects Semantic and Hybrid search; full papers and source links remain intact. See [implementation](docs/SEMANTIC_CHUNKING.md) and [current collection checks](docs/COVERAGE_2026_11_04.md).

### October 21 diagnostic repairs

Four specifically identified missing papers were added (two full texts and two abstract-only records), bringing the searchable collection to **2,924 papers**. Incremental indexing reused **98,131 vectors** and encoded **225 new vectors**. Relevance ranking now considers 30 candidates using query-focused abstracts, with explicit token limits and scientific vocabulary for muscle-growth questions.

Local summaries reject titles as findings, exclude primary-study background/discussion from claims about that study's results, expose exact methods/population context, and reject the observed paper-wide absence claims and lost uncertainty. Identical section readings can be reused across corpus expansions; a transient local connection timeout is retried once.

On the **same three development questions**, AI-assisted P@10 rose from 66.7% to 90.0%; P@3 rose from 77.8% to 100.0%, and P@5 from 73.3% to 86.7%. This targeted repair check is not independent validation or proof of general accuracy. Per-paper judgments are in `evaluation/audit-gap-repair/`; [functional checks](docs/checks/audit-gap-repair.json) preserve the measurements. The final summaries each retained only one finding, and the cereal answer still simplified baseline-age context. These are remaining limitations, not evidence of complete answer accuracy. Historical report scores remain unchanged.
