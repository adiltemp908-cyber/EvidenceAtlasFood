# EvidenceAtlas Food

## 01 / Project update

### From food questions to inspectable research

**Updated project report | November 5, 2026 | CSD358, Track T6**

Adil Muhammed | Roll No. 2410110018

EvidenceAtlas Food is a local literature search, study comparison and evidence-reading application. It discovers nutrition papers, preserves their source passages, retrieves relevant studies using lexical and neural methods, and lets readers inspect the evidence behind each result. Everyday, dietitian and research views expose different levels of detail over the same collection.

Since the October report, the project has expanded its collection, removed truncation from semantic embedding inputs through overlapping chunks, improved reranking inputs, and added optional local language-model summaries. The November 4 update makes Hybrid + relevance reranking the opening default and adds direct-applicability checks before an answer is shown.

| Current resource | Verified snapshot |
| --- | --- |
| Collected records | 3,723 |
| Searchable papers | 3,493 |
| Full-text records / searchable full texts | 1,475 / 1,429 |
| Stored source passages | 102,752 |
| Semantic vectors | 115,883 |
| Saved investigations preserved during activation | 19 |

These collection figures describe the November 4 activation, the latest recorded collection state at this report date. Total records include held or unavailable material; searchable counts describe the active retrieval collection. Semantic vectors can outnumber passages because long passages produce multiple chunks.

**What this report establishes:** implemented behavior, measured collection growth, reproducible historical retrieval scores, and recorded functional checks. It does not claim an independently measured accuracy score for the expanded collection or the local summarizer.

The original report and published final-report PDFs remain available as historical artifacts. This report supersedes their descriptions of the current implementation.

Sources: docs/STATUS.md; docs/COVERAGE_2026_11_04.md; docs/checks/coverage-2026-11-04.json.

## 02 / Collection growth and provenance

### A larger, resumable literature collection

PubMed subject headings and Europe PMC title/abstract queries cover foods, nutrients, preparation, meal timing and everyday dietary questions. Acquired records retain identifiers, raw provider responses and provenance. Open-access JATS XML is parsed into section-linked passages; abstract-only and metadata-only availability remain explicit.

| Snapshot | Records | Searchable | Full texts* | Passages |
| --- | --- | --- | --- | --- |
| October 7 | 973 | 950 | 494 | 37,975 |
| October 13 | 1,866 | 1,796 | 839 | 60,420 |
| October 19 | 2,392 | 2,291 | 1,022 | 73,347 |
| October 20 | 3,054 | 2,920 | 1,213 | 86,903 |
| October 23 batch | 3,534 | 3,352 | 1,386 | 97,245 |
| November 4 | 3,723 | 3,493 | 1,475 | 102,752 |

*Full texts in this timeline count collected full-text records, including records outside active search. The October 23 batch was activated on October 24. Four targeted audit-gap papers were added between the October 20 and October 23 snapshots.

The product expansion added coverage of creatine, plant milks, nuts and seeds, fish oil, magnesium, collagen, psyllium, probiotics, sports drinks and whey products. Subsequent batches broadened topic and publication-period coverage.

The latest everyday-diet batch acquired 189 new records. After provisional scope checks, 141 entered search, including 81 full texts and 28 papers on water intake or hydration. Its eleven topics cover sugar, breakfast, coffee, dairy tolerance, fiber, fruit and vegetables, water, protein, salt and staple grains. Topic counts overlap because a paper can belong to more than one topic.

Forty-eight new records remain outside search. Screening holds identified animal/veterinary, contamination, protocol, industrial and perception-only material for review. Unknown species metadata does not automatically exclude papers with a human context. These are rule-based and AI-assisted decisions, not expert screening.

Incremental builds reuse unchanged vectors and keep resumable checkpoints. The latest build reused 109,628 vectors and encoded 6,255 new ones. Corpus/index checks precede activation; rollback snapshots and all 19 saved investigations were retained.

Sources: README.md collection timeline; docs/COLLECTION_CONTINUATION.md; docs/PRODUCT_EXPANSION.md; docs/COVERAGE_2026_11_04.md.

## 03 / Retrieval and semantic coverage

### Match words, meaning and scientific context

| Stage | Current behavior |
| --- | --- |
| Lexical retrieval | Boolean and positional phrase search, TF-IDF, flat BM25 and section-aware BM25 |
| Semantic retrieval | all-MiniLM-L6-v2; 384-dimensional vectors; best matching chunk per paper |
| Hybrid fusion | Reciprocal Rank Fusion of lexical and semantic candidates |
| Relevance reranking | MiniLM cross-encoder; up to 30 candidates with query-focused abstracts and bounded inputs |
| Optional recency | Capped 3% bonus after relevance ranking; halves every five years |
| Inspection | Source passages, filters, scores, expansions and corpus identity exposed in research traces |

Long source passages now use overlapping tokenizer-bounded windows, with a 256-token input limit including special tokens and 32 source tokens of overlap. Each chunk keeps original character offsets and is checked again against the model limit. The current index contains 115,883 vectors from 102,752 source passages, with zero truncated semantic inputs in the recorded activation.

Chunking preserves the full original passage, paper identity, lexical search and source navigation. Multiple chunks from one paper do not occupy multiple paper-result positions. Hybrid results retain the matching span, so the reader can move from a specific hit to its complete surrounding passage.

Reusable vectors must match the complete input, source identity, pinned model and token settings. Changed or new inputs are encoded separately. This makes later collection growth practical without silently reusing stale representations.

The October 21 reranker update increased the candidate budget to 30 and uses query-focused abstract inputs with explicit token limits. Scientific vocabulary expansion also covers muscle-growth questions. The reranker still reads bounded input; it does not evaluate entire papers or establish scientific truth.

Hybrid + relevance reranking is now selected when both capabilities are available. Missing reranking falls back to Hybrid; a missing dense index falls back to section-aware BM25. Users can change methods under Refine search. The optional newer-paper preference can be disabled for relevance-only comparisons.

Sources: docs/SEMANTIC_CHUNKING.md; docs/PRODUCT_EXPANSION.md; docs/checks/audit-gap-repair.json; docs/LOCAL_SUMMARIES.md.

## 04 / Local summaries and applicability

### Read selected papers, then inspect the quotations

After searching, the user chooses 1-10 papers, defaulting to 3, and selects Summarize. The locally hosted Qwen3-4B-Instruct-2507 model reads every stored passage of those selected papers in bounded groups. The optional GPU reader operates separately from MiniLM retrieval and does not change search rankings.

| Step | Constraint and visible result |
| --- | --- |
| Prepare | Validate paper IDs and corpus identity; tokenize groups within the 8,192-token context |
| Extract | Retain exact quotations and source offsets; reject fabricated quotations |
| Select | Check requested exposure, outcome and explicit population, dose, timing and comparator |
| Draft and verify | Require quotation support and direct applicability; suppress unsupported answers |
| Inspect | Show source links, reading coverage, retained quotations and context |

Pipeline v9 abstains when it cannot identify findings that directly answer the question in the selected papers. Related quotations remain inspectable. Its absence statement is restricted to the selected papers and available text; it does not imply that no relevant studies exist elsewhere. Direct null findings remain eligible.

Source-role checks reject titles as findings and primary-study background or discussion as evidence of that study's own results. Exact descriptive passages can supply participant or intervention context. Guards address observed confusion between an excerpt and a whole paper, trial/review attribution, and loss of uncertainty wording. Review synthesis retains review attribution.

Completed identical summaries are cached. Matching section readings can be reused when the paper count changes or unrelated literature is added. Tokenization plans are cached when source text and tokenizer inputs match. Old completed answers require regeneration after the pipeline change. Stop reading preserves completed section work; one transient local connection failure is retried.

Reading every stored passage does not preserve every finding: extraction and final answer budgets compress the material. Figures and unavailable full texts cannot be read. Applicability and support checks remain fallible model judgments; exact citations do not guarantee correct interpretation.

Runtime: Q4_K_M model, pinned llama.cpp b11753 Windows Vulkan build, one summary job at a time, loopback service and 120-second idle unload. No paid inference API is required.

Sources: docs/LOCAL_SUMMARIES.md; docs/checks/local-summary.json; docs/checks/summary-speed.json; docs/checks/summary-applicability-2026-11-04.json.

## 05 / Application and reproducibility

### An inspectable workflow backed by local storage

The interface carries a question from search to evidence inspection. Results identify source availability; opening a paper reveals passages and surrounding sections. Users can compare up to four studies, save investigations with notes, and export evidence. Everyday explanations, dietitian context and research diagnostics share the same underlying papers.

The updated summary controls expose the selected paper count, reading progress, cancellation, cached work and exact source quotations. A completed answer records the papers actually read. Smaller selections reduce work and evidence coverage. Cached duration is labeled as the original reading time, rather than presented as a fresh run.

| Repository component | Responsibility |
| --- | --- |
| evidenceatlas/ | Acquisition, parsing, screening, indexing, ranking, local API and summary pipeline |
| web/ | Browser interface; TypeScript and compiled JavaScript |
| scripts/ | Resumable collection, index publication, model setup, evaluation and packaging |
| tests/ | Retrieval, chunking, incremental reuse, recency, summary evidence and cache checks |
| evaluation/ | Frozen queries, rankings, relevance judgments and evaluation protocols |
| docs/ | Current and historical reports, design records and measured checks |

The source folder is distinct from the data volume. EAF_ROOT holds downloaded literature, SQLite data, model weights, indexes, private investigations, generated summaries, caches and rollback snapshots. These resources are excluded from the source package and Git changes.

The source archive includes a per-file SHA-256 manifest and is checked after creation. Compiled browser JavaScript is included so a user can run the application without installing Node.js. Report generation uses ReportLab; that dependency is separate from application runtime requirements.

The source release cannot recreate the identical current corpus by itself: fresh acquisition can return a different collection. Frozen evaluation artifacts reproduce the historical scoring independently of new downloads. Acquisition checkpoints and local rollback resources support continuation on the configured machine.

Sources: README.md; scripts/package_source.py; docs/SETUP_REFERENCE.md; docs/LOCAL_SUMMARIES.md.

## 06 / Evaluation: what the scores mean

### Historical relevance scores remain historical

Precision@k is the number of directly relevant results among the first k divided by k. Grade 2 counts as relevant; grade 1 is related background or a contextual mismatch; grade 0 is off-topic. These labels assess retrieval usefulness, not study validity or certainty.

The original report saved twelve searches: six original questions, four rewrites and two matched BM25 baselines. Ten runs were graded, covering 100 ranked positions and 79 unique topic-paper pairs. Two rewrites were screened only. Judgments were AI-assisted, without an independent human gold standard.

| Frozen evaluation group | P@3 | P@5 | P@10 |
| --- | --- | --- | --- |
| Six original questions | 88.9% | 76.7% | 63.3% |
| Five selected presentation examples | 86.7% | 80.0% | 76.0% |
| Two paired BM25 queries | 100.0% | 70.0% | 75.0% |
| Same two queries, hybrid + reranking | 83.3% | 90.0% | 85.0% |

The five presentation examples were selected after inspection. The two-query comparison is too small to establish general superiority. These scores were reproduced from the saved artifacts on November 5; they do not evaluate the expanded November collection.

The October 21 targeted repair check used the same three development questions before and after changes. AI-assisted P@10 increased from 66.7% to 90.0%, P@3 from 77.8% to 100.0%, and P@5 from 73.3% to 86.7%. This is a development comparison after identified failures, not a held-out benchmark. The final summaries retained one finding each, and the cereal answer still simplified baseline-age context.

A chunking diagnostic recovered the source paper in the first ten results for 11/12 excerpt queries before and 12/12 after the change. These source-recovery probes are not independently judged nutrition questions.

The November expansion has functional search checks and saved development rankings, but no new independently judged precision score. Some everyday questions still retrieve tangential studies highly. A larger corpus alone cannot demonstrate higher retrieval accuracy.

Sources: evaluation/report-v2/metrics.json; scripts/evaluate_report.py; evaluation/audit-gap-repair/; docs/SEMANTIC_CHUNKING.md.

## 07 / Verification and known limits

### Separate fresh checks from recorded measurements

**November 5 release checks:** 77 focused regression tests passed across core and dense retrieval, incremental reuse, recency, chunking, everyday topics, summarization, source-evidence checks and summary speed controls. TypeScript passed its no-emit compile check. The historical report metrics were recomputed from saved rankings and judgments.

The legacy live API test was not included: it assumes an older audit matches the active corpus and writes an investigation. No new real-model summary benchmark or live browser run is claimed for this release. Existing measurements below describe their recorded dates and conditions.

| Recorded check | Evidence and scope |
| --- | --- |
| November 4 collection | 36 regression tests; six live searches; 82 exact passages across 29 papers; 19 investigations preserved |
| November 4 applicability | 35 focused tests; browser defaults/fallbacks; eight synthetic selection cases; two complete synthetic pipelines with the installed model |
| October 21 repair | 64 regression checks and a browser check; three development-question comparisons |
| Initial local summary | One green-tea question; 4 full texts + 6 abstracts; 134,332 source characters in 20 groups; all 21 retained quotes checked |

The recorded green-tea full-reading run took 167.9 seconds. A later run reused its section extractions and regenerated two checked paragraphs in 11.4 seconds. These are different cache conditions and one query, not a general latency benchmark. Paper count and cache-plan timings likewise do not measure cold-start performance.

**Remaining limitations:** incomplete and uneven topic coverage; provisional screening; contextual mismatch among retrieved studies; bounded reranker inputs; model omission or misinterpretation of findings; and limited external validation. One applicability verifier rejected an indirect answer but also incorrectly marked its faithful quotation unsupported. This diagnostic error is retained in the check record.

Broader held-out relevance judgments, expert study-context review and independent summary-accuracy evaluation remain needed. Claim truth, causal certainty and study quality are not established by a high relevance score or a passing quotation check.

Sources: docs/checks/release-2026-11-05.json; docs/checks/coverage-2026-11-04.json; docs/checks/summary-applicability-2026-11-04.json; docs/OPEN_ISSUES.md.

## 08 / Setup and continuation

### Run the updated source with the local data volume

Use the project's Python environment with requirements.txt and requirements-models.txt installed. Development used Python 3.13 on Windows. Set EAF_ROOT to the data volume and run from the repository folder:

```powershell
$env:EAF_ROOT = 'E:\EvidenceAtlasFood'
python -m evidenceatlas.cli serve --port 8765
```

Open http://127.0.0.1:8765/ or use the included Windows launcher. Opening web/index.html alone does not start the API. Existing corpus, models and matching indexes can be reused. A clean installation requires acquisition, lexical indexing, model download and dense indexing as documented in README.md.

For optional local summaries on a compatible Windows x64 NVIDIA/Vulkan system, run python scripts/setup_summarizer.py. The pinned model and runtime require roughly 2.5 GB of downloads. The recorded setup used an RTX 4050 Laptop GPU with 6 GB VRAM and about 16 GB system RAM; measured model GPU use was approximately 3.8 GB. First uncached readings can take minutes.

### Reproduce checks and delivery artifacts

```text
python scripts/evaluate_report.py
python scripts/build_report.py
python scripts/package_source.py
```

Report generation requires reportlab==4.4.9. The current report source is docs/REPORT_2026_11_05.md, and the dated PDF is docs/EvidenceAtlas_Food_Report_2026_11_05.pdf. The standard report link is refreshed to the same content. The original October report and previously published final-report PDFs remain available.

Continue acquisition with a new run name, review provisional screening, build incremental embeddings and validate the corpus/index pair before activation. Do not modify an already published expansion run. Default storage guards budget 160 GB and reserve 40 GB free; these are limits rather than download targets.

The next evaluation should freeze the current collection, use new questions and independent reviewers, and assess retrieval relevance separately from answer support, context applicability and omitted counterevidence. Retain null findings and distinguish missing context from explicit mismatch.

Project implementation and documentation used AI assistance. Attribution and the existing demo link are preserved from the published repository. Source hosting is not deployment of the local application or its data.

Sources: README.md; docs/SETUP_REFERENCE.md; docs/COLLECTION_CONTINUATION.md; docs/LOCAL_SUMMARIES.md.
