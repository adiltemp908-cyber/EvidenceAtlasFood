# EvidenceAtlas Food

**Scientific literature retrieval and source-grounded summaries for everyday food and nutrition questions**

**[Video Link](https://drive.google.com/drive/folders/1J2qyEUmowNZrV7AOvcICCEFa07_YCeAx?usp=drive_link)**  
**[Read Final Report](report.pdf)**

EvidenceAtlas Food is a local information-retrieval and study-comparison system with source-grounded summaries, developed to answer nutrition-related questions using evidence from research papers, helping users distinguish scientifically supported findings from common misconceptions and misinformation circulated online. This can be used by students and researchers studying nutrition, healthcare professionals and dieticians seeking research-backed insights, and members of the public looking to make informed dietary choices.

It turns everyday food and nutrition questions into searches across scientific literature and helps users inspect the evidence behind the retrieved results rather than only returning paper titles.

The system combines:

- lexical retrieval
- section-aware BM25
- TF-IDF cosine retrieval
- semantic vector search
- hybrid retrieval
- relevance reranking
- source-grounded summaries with a local LLM

Retrieved papers can be opened at relevant source passages, compared side by side, summarised with links to exact source quotations, saved into investigations and exported for later use.

---

## Project overview

EvidenceAtlas Food was designed around a simple workflow:

1. **Collect scientific literature**
   - Discover nutrition-related papers from PubMed and Europe PMC.
   - Search using scientific subject headings and title/abstract terms.

2. **Preserve paper structure**
   - Store abstracts and, where available, full-text sections such as methods, results and discussion.
   - Break papers into searchable passages while retaining their section and position.

3. **Build multiple retrieval methods**
   - Match exact terminology using lexical retrieval.
   - Match related wording using semantic embeddings.
   - Combine both approaches using hybrid search.

4. **Rerank promising results**
   - Merge lexical and semantic candidates.
   - Apply a relevance model to the strongest candidates to improve final ordering.

5. **Make results inspectable**
   - Open source passages.
   - Navigate surrounding paper sections.
   - Compare studies.
   - Save investigations and export evidence.

6. **Summarise selected papers**
   - Use a local LLM to read the stored sections of the selected papers.
   - Generate a short answer linked to exact source quotations.
   - Check quotation support and direct applicability; state when no direct answer is identified in the selected evidence.

7. **Evaluate retrieval quality**
   - Review ranked papers.
   - Compare precision, recall, F1, MAP and nDCG at rank 10.

---

## Current corpus

As of the November 4, 2026 expansion, the project collection contains:

| Resource | Count |
|---|---:|
| Unique records | 3,723 |
| Searchable papers | 3,493 |
| Full-text records | 1,475 |
| Searchable full-text papers | 1,429 |
| Section passages | 102,752 |
| Semantic vectors | 115,883 |

Of the collected records:

- **1,475** contain ingested full text.
- **2,222** contain abstracts only.
- **26** contain metadata only.

The latest batch added 141 searchable papers across eleven everyday-diet topics, including 28 papers about water intake and hydration. See [collection updates](docs/COVERAGE_2026_11_04.md).

Evidence availability is shown explicitly in the interface so that an abstract-only record is not presented as though the complete paper was inspected.

When open-access full text is available, JATS XML is downloaded and parsed. Each stored passage retains its parent paper, section name and position, allowing users to move from a search result to the surrounding scientific context.

---

## Search methods

EvidenceAtlas Food implements **six selectable retrieval techniques**. An optional local LLM summary step reads selected papers after retrieval without changing their search rankings.

### 1. Section-Aware BM25

BM25 lexical retrieval with additional awareness of where terms occur inside a paper.

A match in a results section, for example, can be treated differently from a match in general background text.

### 2. Flat BM25

Standard BM25 retrieval over indexed text without section-specific weighting.

### 3. Flat TF-IDF Cosine

TF-IDF vectors are compared using cosine similarity to identify papers containing similar term distributions.

### 4. Semantic Search

Passages are encoded using **MiniLM embeddings**.

Each passage is represented as a **384-dimensional vector**, and the user's question is encoded in the same space. This allows related wording to match even when the exact words in the question do not occur in the paper.

The current dense index contains **115,883 semantic vectors** from **102,752 source passages**.

Long passages are split into overlapping chunks that fit the model's 256-token input limit, with no truncated embedding inputs in the current index. Complete source passages remain available for reading and lexical search. See [semantic chunking](docs/SEMANTIC_CHUNKING.md).

### 5. Hybrid Search

Hybrid search combines lexical and semantic rankings so that the system can benefit from both:

- exact scientific terminology
- semantic similarity

The rankings are combined using **Reciprocal Rank Fusion**.

### 6. Hybrid + Relevance Ranking

This is the strongest retrieval pipeline currently implemented.

First, hybrid retrieval creates a candidate set using lexical and semantic search. A MiniLM cross-encoder then examines up to 30 candidates using:

- the user's question
- the paper title
- a query-focused abstract or selected source passage within explicit token limits

The cross-encoder reranks the candidates according to estimated relevance.

The reranker determines how closely a result relates to the question. It does **not** determine whether a scientific claim is true.

Hybrid + relevance ranking is now the opening default when available, with fallbacks for missing model/index capabilities. **Refine search** also offers an optional newer-paper preference, capped at 3%, which can be turned off for relevance-only comparisons.

---

## Using the application

EvidenceAtlas Food provides a local browser interface for searching, inspecting and summarising scientific evidence.

A result card shows the paper together with its evidence availability.

Opening a result allows the user to inspect relevant passages and surrounding sections.

The interface also supports:

- paper comparison
- source navigation
- saved investigations
- notes
- evidence export
- retrieval diagnostics
- source-grounded summaries with inspectable quotations
- summary paper-count selection, reading progress, cancellation and cached results

Up to **four papers** can be compared together.

After searching, choose **1-10 papers** (default **3**) and click **Summarize** to have the optional local Qwen3 model read their stored sections. Answers link to exact quotations; reading progress, cancellation and cached results are available. If the selected evidence does not directly answer the question, the application says so. See [local summaries](docs/LOCAL_SUMMARIES.md).

The application is intended to support several levels of use:

### Everyday users

Ask a food or nutrition question, read a source-grounded summary and inspect the papers and quotations behind it.

### Dietitians

Review study context and compare multiple papers addressing the same question.

### Researchers

Inspect retrieval traces, ranking behaviour, summary source quotations and experimental model diagnostics.

---

## Evaluation

On 15 November 2026, six search methods ran the same ten questions against a collection of 3,493 searchable papers. Query expansion was enabled and the recency preference was disabled. The top ten results from each search yielded 600 ranked positions and 310 distinct question–paper pairs.

### Hybrid + reranker results by question

The first five questions were graded easy and the last five medium. Precision@10 counts the share of the first ten papers that directly address the question, including useful partial matches (grades 2 and 3). nDCG@10 gives more weight to highly relevant papers near the top.

| # | Question | Precision@10 | nDCG@10 |
|---:|---|---:|---:|
| 1 | Does drinking coffee affect sleep? | 100% | 0.868 |
| 2 | Does reducing salt intake lower blood pressure? | 80% | 0.862 |
| 3 | Does eating more fiber help with constipation? | 90% | 0.934 |
| 4 | Does drinking milk help keep bones strong? | 90% | 0.903 |
| 5 | Does boiling vegetables reduce their vitamin C content? | 50% | 0.886 |
| 6 | Does eating oats lower LDL cholesterol? | 60% | 0.754 |
| 7 | Does eating nuts cause weight gain in adults? | 50% | 0.855 |
| 8 | Is yogurt easier to digest than milk for people with lactose intolerance? | 70% | 0.850 |
| 9 | Are sugary drinks linked to type 2 diabetes? | 50% | 0.868 |
| 10 | Does extra protein help build muscle during resistance training? | 100% | 0.927 |
| | **Mean** | **74%** | **0.871** |

Counting only fully applicable papers (grade 3) gives a mean Precision@10 of **50%** for hybrid + reranker.

### Search method comparison

Each score is the mean across all ten questions. Recall, F1 and MAP use the pool of papers returned by the six methods for each question.

| Search method | Precision@10 | Recall@10 | F1@10 | MAP@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| TF-IDF cosine | 50% | 36.5% | 40.0% | 0.268 | 0.680 |
| Flat BM25 | 52% | 37.1% | 41.3% | 0.264 | 0.661 |
| Section-aware BM25 | 45% | 30.3% | 34.6% | 0.213 | 0.618 |
| Semantic search | 73% | 55.0% | 59.7% | 0.484 | 0.829 |
| Hybrid | 64% | 46.2% | 51.2% | 0.382 | 0.776 |
| Hybrid + reranker | 74% | 56.5% | 60.8% | 0.490 | 0.871 |

---

# Running EvidenceAtlas Food

## Quick start

If the project has already been configured on the development machine, double-click:

```text
Open EvidenceAtlas.cmd
```

The launcher can be located in the `app` folder or its parent `EvidenceAtlasFood` folder.

The application opens at:

```text
http://127.0.0.1:8765/
```

Python must be available. The original installation uses an existing Anaconda environment.

The equivalent manual command is:

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
python -m evidenceatlas.cli serve --port 8765
```

Run the command from the `app` directory.

Requirements are recorded in:

```text
requirements.txt
requirements-models.txt
```

Detailed reproduction information is also available in:

```text
docs/SETUP_REFERENCE.md
```

---

## First installation — Windows / PowerShell

Download or clone the repository and open PowerShell inside the source directory.

Python **3.13** was used during development.

The recommended layout is:

```text
E:\EvidenceAtlasFood\
│
├── app\
├── data\
├── indexes\
├── models\
├── cache\
├── experiments\
└── tmp\
```

The Git repository should contain the `app` directory.

Large corpora, indexes, downloaded models and caches should remain outside the repository.

### 1. Configure the data root

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
```

### 2. Prepare cache and temporary directories

```powershell
New-Item -ItemType Directory -Force "$env:EAF_ROOT\cache\pip", "$env:EAF_ROOT\tmp" | Out-Null

$env:PIP_CACHE_DIR = "$env:EAF_ROOT\cache\pip"
$env:TEMP = "$env:EAF_ROOT\tmp"
$env:TMP = $env:TEMP
```

### 3. Create the Python environment

```powershell
python -m venv "$env:EAF_ROOT\.venv"

$py = "$env:EAF_ROOT\.venv\Scripts\python.exe"
```

### 4. Install dependencies

```powershell
& $py -m pip install -r requirements.txt -r requirements-models.txt
```

For optional local summaries on Windows x64 with a compatible NVIDIA/Vulkan GPU, also run:

```powershell
& $py scripts/setup_summarizer.py
```

This downloads approximately 2.5 GB of model/runtime files to `EAF_ROOT`. See [local summary setup and limitations](docs/LOCAL_SUMMARIES.md).

---

## Building a fresh corpus

If the configured data root already contains the corpus, indexes and models, this section can be skipped.

For a fresh installation, begin by acquiring papers:

```powershell
& $py -m evidenceatlas.cli ingest --pages 1 --page-size 25
```

Build the lexical indexes:

```powershell
& $py -m evidenceatlas.cli index
```

Download or initialize the embedding and reranking models:

```powershell
& $py -m evidenceatlas.models embedding reranker
```

Build the dense semantic index:

```powershell
& $py -m evidenceatlas.cli dense-index
```

For the optional research stance diagnostic:

```powershell
& $py -m evidenceatlas.models nli
```

Acquisition and model downloads require internet access.

Paper acquisition and dense embedding generation can take significant time depending on the number of papers being processed.

---

## Expanding the corpus

The ingestion command is an initial batch operation rather than a fixed corpus-size limit.

Running ingestion again resumes discovery.

For a larger time-budgeted acquisition:

```powershell
& $py -m evidenceatlas.cli ingest --pages 0 --seconds 1800
```

After adding new material, rebuild the required indexes.

```powershell
& $py -m evidenceatlas.cli index
& $py -m evidenceatlas.cli dense-index
```

The storage guard reserves **40 GB of free space by default**.

Newly downloaded corpora may differ from the frozen collection used for the report evaluation.

Incremental indexing reuses matching vectors and encodes new or changed passages. For staged collection runs, checks and activation, see [collection continuation](docs/COLLECTION_CONTINUATION.md).

---

## Starting the server

With the virtual environment configured:

```powershell
& $py -m evidenceatlas.cli serve --port 8765
```

Then open:

```text
http://127.0.0.1:8765/
```

Stop the server using:

```text
Ctrl+C
```

Do **not** open `web/index.html` directly. The interface depends on the local Python API and therefore requires the EvidenceAtlas server to be running.

If using a custom Python environment rather than the original project environment, prefer the explicit serve command instead of the convenience launcher.

---

# Current limitations

EvidenceAtlas Food is a working retrieval prototype, but several limitations remain.

## Corpus coverage

The current collection contains thousands of papers rather than the full nutrition literature.

Relevant research can therefore be absent simply because it has not yet been collected.

The most direct improvement is to continue expanding the corpus with additional research papers from PubMed and Europe PMC.

However, corpus growth also increases processing cost. Newly collected full texts must be:

1. parsed
2. divided into passages
3. indexed lexically
4. encoded into embeddings
5. added to the dense vector index

Embedding a substantially larger collection can therefore take considerable computation time.

---

## Relevance reranking

The current strongest pipeline is:

```text
Lexical retrieval
        +
Semantic retrieval
        ↓
Reciprocal Rank Fusion
        ↓
Relevance reranking
```

The current reranker already improves deeper retrieval in several tested queries, but it remains relatively lightweight.

A future version could place a stronger model above hybrid retrieval to evaluate candidate papers with better contextual understanding.

Possible improvements include:

- stronger cross-encoder rerankers
- improved passage selection before reranking
- reranking using multiple passages from the same paper
- better handling of long scientific sections
- models trained more directly for scientific or biomedical relevance

---

## Local LLM summaries

An optional **local large language model**, Qwen3-4B-Instruct-2507, now operates above the retrieval system.

Rather than replacing retrieval, the model operates after relevant papers have already been selected.

For example:

```text
Question
   ↓
Hybrid retrieval
   ↓
Relevance reranking
   ↓
Stored sections of selected papers
   ↓
Local LLM
   ↓
Evidence-grounded explanation
```

The local model currently supports:

- reading every stored section of the selected papers in bounded groups
- extracting findings with exact source quotations
- generating short answers from findings judged directly applicable to the question
- checking quotation support and suppressing answers that fail verification
- reusing completed summaries and matching section readings

Keeping the model local preserves the project's current local-first architecture and avoids requiring a paid inference API.

Generated answers remain linked to inspectable source passages. The current pipeline checks quotation support and direct applicability, and abstains when it cannot identify a direct answer in the selected papers. These checks can still miss errors or relevant findings; independent summary-accuracy validation remains outstanding. Abstract-only papers supply only their available text, and reading all stored sections does not guarantee that every finding survives the summary. First uncached readings can take several minutes.

---

## Passage selection

The reranker currently examines a query-focused abstract or selected passage rather than the complete paper.

This keeps ranking practical but can miss information located elsewhere in the study.

Future versions could improve the selection of evidence passages or allow multiple sections from a paper to contribute to the final relevance score.

---

## Scientific interpretation

EvidenceAtlas Food ranks literature according to relevance and can summarise selected evidence with source quotations.

It does not independently determine:

- whether a claim is scientifically true
- whether a study is high quality
- whether evidence is causal
- the certainty of a scientific conclusion
- whether medical or nutritional advice should be followed


---

# Possible future improvements

The main next steps are:

- increase the number of collected research papers
- expand the number of full-text sources
- continue incremental embedding updates as the corpus grows
- improve passage selection
- experiment with stronger reranking models
- improve scientific query rewriting
- evaluate more questions across different nutrition topics
- construct a larger relevance benchmark
- compare additional retrieval and reranking models

---

# Repository structure

| Folder | Contents |
|---|---|
| `evidenceatlas/` | Python retrieval, ingestion, local LLM summaries and local API |
| `web/` | HTML/CSS and TypeScript interface; compiled JavaScript included |
| `scripts/` | Launch, evaluation, packaging and report utilities |
| `tests/` | Retrieval, summary evidence, caching and interface checks |
| `evaluation/` | Protocols, queries, saved rankings and review materials |
| `docs/` | Project documentation, report and demonstration material |
| `docs/checks/` | Development and verification results |
| `docs/screenshots/` | Application screenshots |

Only the **`app`** source directory belongs in the GitHub repository.

The parent project directory stores large local resources:

```text
data/
indexes/
models/
cache/
experiments/
tmp/
```


---

# Verification

Run the core retrieval tests:

```powershell
python -m pytest tests/test_core.py tests/test_dense.py -q
```

The November 5 delivery check passed **77 focused regression tests**, covering retrieval, chunking, incremental indexing, recency and summaries, plus TypeScript checking. See [release checks](docs/checks/release-2026-11-05.json) for the exact commands and scope.

Earlier browser checks also exercised:

- search
- source inspection
- study comparison
- saved investigations
- evidence export

---

# Packaging the source

Run:

```powershell
python scripts/package_source.py
```

The packaging process is intended to create the source distribution without including the large local corpus, indexes, models or private investigations.

---

# Project report

[Read the eight-page project report (PDF)](report.pdf).

---

# Course materials

Project documentation is available under `docs/`.

Important files include:

- [Project report](report.pdf)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Setup and reproduction reference](docs/SETUP_REFERENCE.md)
- [Course requirements](docs/COURSE_REQUIREMENTS.md)
- [Original specification](docs/SPECIFICATION.md)
- [Agreed delivery scope](docs/DELIVERY_SCOPE.md)
- [Project status](docs/STATUS.md)
- [Open issues](docs/OPEN_ISSUES.md)
- [Local summaries and limitations](docs/LOCAL_SUMMARIES.md)
- [Evaluation protocol](evaluation/PROTOCOL.md)

---


Rather than indexing unrestricted web pages, it operates specifically on food and nutrition research literature and makes use of scientific-document structure including:

- sections
- passages
- metadata
- source identifiers
- citations
- full-text availability

The system can support professional users such as dietitians and researchers while remaining accessible to people asking everyday food questions.

The project also incorporates elements associated with retrieval and machine-learning systems, including embeddings, vector similarity, hybrid ranking, neural relevance reranking and source-grounded summaries generated by a local LLM.

---

## Project

**EvidenceAtlas Food**  
*From food questions to scientific evidence.*

**Adil Muhammed**  
