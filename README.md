# EvidenceAtlas Food

**Scientific literature retrieval for everyday food and nutrition questions**

**[Video Link](https://drive.google.com/drive/folders/1J2qyEUmowNZrV7AOvcICCEFa07_YCeAx?usp=drive_link)**  
**[Read Final Report](https://github.com/adiltemp908-cyber/EvidenceAtlasFood/blob/main/EvidenceAtlasFood-Report-Final.pdf)**

EvidenceAtlas Food is a local information-retrieval and study-comparison system developed for **CSD358 — Track T6**.

It turns everyday food and nutrition questions into searches across scientific literature and helps users inspect the evidence behind the retrieved results rather than only returning paper titles.

The system combines:

- lexical retrieval
- section-aware BM25
- TF-IDF cosine retrieval
- semantic vector search
- hybrid retrieval
- relevance reranking

Retrieved papers can be opened at relevant source passages, compared side by side, saved into investigations and exported for later use.

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

6. **Evaluate retrieval quality**
   - Review ranked papers.
   - Measure Precision@3, Precision@5 and Precision@10.

---

## Current corpus

The frozen project collection contains:

| Resource | Count |
|---|---:|
| Unique records | 973 |
| Searchable papers | 950 |
| Full-text papers | 494 |
| Section passages | 37,975 |
| Nutrition topic groups | 12 |

Of the collected records:

- **494** contain ingested full text.
- **473** contain abstracts only.
- A small number contain metadata only.

Evidence availability is shown explicitly in the interface so that an abstract-only record is not presented as though the complete paper was inspected.

When open-access full text is available, JATS XML is downloaded and parsed. Each stored passage retains its parent paper, section name and position, allowing users to move from a search result to the surrounding scientific context.

---

## Search methods

EvidenceAtlas Food implements **six selectable retrieval techniques**.

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

The current dense index contains embeddings for all **37,975 passages**.

The embedding model reads up to 256 tokens from a passage. Longer passages remain fully available through lexical search even when their dense representation uses truncated input.

### 5. Hybrid Search

Hybrid search combines lexical and semantic rankings so that the system can benefit from both:

- exact scientific terminology
- semantic similarity

The rankings are combined using **Reciprocal Rank Fusion**.

### 6. Hybrid + Relevance Ranking

This is the strongest retrieval pipeline currently implemented.

First, hybrid retrieval creates a candidate set using lexical and semantic search. A MiniLM cross-encoder then examines up to 20 candidates using:

- the user's question
- the paper title
- a selected source passage

The cross-encoder reranks the candidates according to estimated relevance.

The reranker determines how closely a result relates to the question. It does **not** determine whether a scientific claim is true.

---

## Using the application

EvidenceAtlas Food provides a local browser interface for searching and inspecting scientific evidence.

A result card shows the paper together with its evidence availability.

Opening a result allows the user to inspect relevant passages and surrounding sections.

The interface also supports:

- paper comparison
- source navigation
- saved investigations
- notes
- evidence export
- retrieval diagnostics

Up to **four papers** can be compared together.

The application is intended to support several levels of use:

### Everyday users

Ask a food or nutrition question and inspect scientific papers related to it.

### Dietitians

Review study context and compare multiple papers addressing the same question.

### Researchers

Inspect retrieval traces, ranking behaviour and experimental model diagnostics.

---

## Evaluation

The report evaluates retrieval using **Precision@k**.

```text
Precision@k = relevant papers in the first k results / k
```

Only papers judged directly useful for addressing the question are counted as relevant.

The evaluation uses three grades:

| Grade | Meaning |
|---|---|
| 2 | Relevant — directly useful for answering part of the question |
| 1 | Related — useful background or partial mismatch |
| 0 | Off-topic |

Only **grade 2** contributes to reported precision.

The judgments measure **retrieval relevance**, not the scientific validity, certainty or quality of the underlying study.

### Selected report examples

| Query | P@3 | P@5 | P@10 |
|---|---:|---:|---:|
| Does coffee affect sleep? | 100.0% | 100.0% | 90.0% |
| Is eating a late night meal bad? | 100.0% | 80.0% | 80.0% |
| Does boiling vegetables remove vitamins? | 66.7% | 60.0% | 80.0% |
| Dietary sodium reduction blood pressure clinical trials | 66.7% | 80.0% | 80.0% |
| Does drinking milk help keep bones strong? | 100.0% | 80.0% | 50.0% |
| **Selected-example mean** | **86.7%** | **80.0%** | **76.0%** |

These examples were selected after inspection and are included as a demonstration rather than as a general accuracy estimate.

Across the original six-question set, including the weaker egg query, the reported averages were:

- **P@3: 88.9%**
- **P@5: 76.7%**
- **P@10: 63.3%**

---

## Query refinement

The project also demonstrates that better queries can materially change retrieval behaviour.

For example:

```text
Does eating salt raise blood pressure?
```

was rewritten as:

```text
Dietary sodium reduction blood pressure clinical trials
```

For this example, Precision@10 increased from **60% to 80%**, although Precision@3 decreased from **100% to 66.7%**.

This demonstrates that adding scientific specificity can retrieve more useful papers overall without necessarily improving every ranking position.

---

## Baseline comparison

A small paired comparison was performed using the coffee/sleep query and the refined sodium query.

| Method | P@3 | P@5 | P@10 |
|---|---:|---:|---:|
| Flat BM25 | 100.0% | 70.0% | 75.0% |
| Hybrid + relevance ranking | 83.3% | 90.0% | 85.0% |

Hybrid + relevance ranking performed better at ranks 5 and 10, while BM25 performed better at rank 3.

Because this comparison contains only two queries, it should not be interpreted as evidence that one method is universally superior.

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

# Reproducing the report evaluation

Run:

```powershell
python scripts/evaluate_report.py
```

The current report evaluation is stored under:

```text
evaluation/report-v2/
```

It contains:

- six original questions
- four query rewrites
- two matched BM25 baseline searches

A total of **12 searches** were saved.

Ten runs were graded, covering:

- 100 ranked result positions
- 79 unique topic-paper pairs

The other two rewritten searches were screened but do not have claimed precision scores.

The five examples shown in the project report were selected after inspection.

Their mean performance is:

```text
P@3  = 86.7%
P@5  = 80.0%
P@10 = 76.0%
```

These values are an exploratory demonstration.

They should not be interpreted as:

- a held-out benchmark
- an independent human gold standard
- a measure of scientific truth
- a clinical accuracy score

The older ten-question, six-method evaluation remains available under:

```text
evaluation/everyday-10/
```

It can be reproduced using:

```powershell
python scripts/evaluate_everyday.py
```

Its labels and scores belong to a separate earlier evaluation and should not be mixed with the report-v2 results.

---

# Current limitations

EvidenceAtlas Food is a working retrieval prototype, but several limitations remain.

## Corpus coverage

The current collection contains hundreds of papers rather than the full nutrition literature.

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

## Local LLM layer

Another possible extension is a **local large language model** operating above the retrieval system.

Rather than replacing retrieval, the model could operate after relevant evidence has already been selected.

For example:

```text
Question
   ↓
Hybrid retrieval
   ↓
Relevance reranking
   ↓
Selected scientific passages
   ↓
Local LLM
   ↓
Evidence-grounded explanation
```

A local model could potentially help with:

- explaining retrieved evidence
- comparing findings across studies
- summarising agreements and disagreements
- generating evidence-grounded responses
- assisting with query reformulation

Keeping the model local would also preserve the project's current local-first architecture and avoid requiring a paid inference API.

Any generated answer should remain linked to inspectable source passages rather than replacing them.

---

## Passage selection

The reranker currently examines a selected passage rather than the complete paper.

This keeps ranking practical but can miss information located elsewhere in the study.

Future versions could improve the selection of evidence passages or allow multiple sections from a paper to contribute to the final relevance score.

---

## Scientific interpretation

EvidenceAtlas Food ranks literature according to relevance.

It does not independently determine:

- whether a claim is scientifically true
- whether a study is high quality
- whether evidence is causal
- the certainty of a scientific conclusion
- whether medical or nutritional advice should be followed

Automated stance and claim analysis remains experimental.

Small AI-assisted relevance audits are diagnostic tools rather than independent human scientific validation.

---

# Possible future improvements

The main next steps are:

- increase the number of collected research papers
- expand the number of full-text sources
- regenerate embeddings for the expanded corpus
- improve passage selection
- experiment with stronger reranking models
- test a local LLM above hybrid + relevance ranking
- improve scientific query rewriting
- evaluate more questions across different nutrition topics
- use independent human reviewers
- construct a larger relevance benchmark
- compare additional retrieval and reranking models

A larger model alone will not solve missing evidence. Retrieval quality depends on both the quality of the ranking system and the coverage of the underlying corpus.

---

# Repository structure

| Folder | Contents |
|---|---|
| `evidenceatlas/` | Python retrieval, ingestion and local API |
| `web/` | HTML/CSS and TypeScript interface; compiled JavaScript included |
| `scripts/` | Launch, evaluation, packaging and report utilities |
| `tests/` | Retrieval and interface checks |
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

These are excluded from the source repository.

The data root should remain on `E:` for the original project configuration.

Do not commit private saved investigations.

---

# Verification

Run the core retrieval tests:

```powershell
python -m pytest tests/test_core.py tests/test_dense.py -q
```

The final delivery check reported that the core/dense tests and TypeScript check passed.

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

# Rebuilding the project report

The generated project report is already included in the repository.

To rebuild it, install:

```text
reportlab==4.4.9
```

Then run:

```powershell
python scripts/build_report.py
```

The report uses the EvidenceAtlas website palette and local Georgia/Segoe UI fonts when available, with bundled PDF fonts as fallback.

ReportLab is not required to run EvidenceAtlas Food itself.

---

# Course materials

Project documentation is available under `docs/`.

Important files include:

- [Project report](docs/EvidenceAtlas_Food_Report.pdf)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Setup and reproduction reference](docs/SETUP_REFERENCE.md)
- [Course requirements](docs/COURSE_REQUIREMENTS.md)
- [Original specification](docs/SPECIFICATION.md)
- [Agreed delivery scope](docs/DELIVERY_SCOPE.md)
- [Project status](docs/STATUS.md)
- [Open issues](docs/OPEN_ISSUES.md)
- [Evaluation protocol](evaluation/PROTOCOL.md)

---

# Track T6

EvidenceAtlas Food fits **CSD358 Track T6** because it is a search system built for a specialised professional domain.

Rather than indexing unrestricted web pages, it operates specifically on food and nutrition research literature and makes use of scientific-document structure including:

- sections
- passages
- metadata
- source identifiers
- citations
- full-text availability

The system can support professional users such as dietitians and researchers while remaining accessible to people asking everyday food questions.

The project also incorporates elements associated with retrieval and machine-learning systems, including embeddings, vector similarity, hybrid ranking and neural relevance reranking.

---

## Project

**EvidenceAtlas Food**  
*From food questions to scientific evidence.*

**Adil Muhammed**  
**Roll No: 2410110018**
