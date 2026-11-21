# EvidenceAtlas Food - Project Report

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
01 / 08
THE PROJECT
EvidenceAtlas Food
From food questions to scientific evidence.
RESEARCH RETRIEVAL AND SOURCE-GROUNDED SUMMARIES
EvidenceAtlas
Food
From a food question to the studies
behind it.
A local search, study comparison and evidence-reading tool for everyday
readers, dietitians and researchers.
WHAT THE SYSTEM DOES
01
Collect real literature
Find nutrition papers in PubMed and Europe PMC.
02
Keep the paper structure
Separate abstracts, methods, results and other sections.
03
Build and combine searches
Match exact terms and meaning, then rank candidate papers.
04
Make the evidence inspectable
Open source passages, compare studies and save an investigation.
05
Summarise selected studies
Read paper sections with a local LLM and link claims to source quotations.
06
Measure retrieval
Review ranked papers and calculate Precision@3, @5 and @10.
3,493 searchable papers
1,429 full texts
102,752 passages

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
02 / 08
01 / COLLECT AND ORGANIZE
Start with the literature.
The collection was built from scientific records, then turned into searchable sections.
3,723
unique records
3,493
searchable papers
1,475
full-text records
We searched by scientific subject headings and by words in titles and abstracts. The topic plan covered
foods, nutrients, meal timing and preparation: for example caffeine and sleep, sodium and blood pressure,
and cooking and vitamin retention.
THE PATH FROM A RECORD TO EVIDENCE
DISCOVER
MeSH + title/abstract
>
SCREEN
Nutrition relevance
>
DEDUPLICATE
PMID / PMCID / DOI
>
PARSE
Sections + passages
When an open-access full text was available, the JATS XML was downloaded and parsed. Each passage keeps
its parent paper, section name and position. This lets a result open at the relevant evidence while the reader
checks the surrounding methods or discussion.
FULL TEXT
More than the abstract
1,429 of these records are searchable. Inspect
methods, results, discussion and tables where
the source supplies them.
ABSTRACT ONLY
A visible limit
2,222 records have abstracts only; 26 contain
metadata only. Availability labels prevent an
abstract from appearing to be a complete paper.
Raw responses and content hashes are retained. The November 4 expansion added 141 searchable papers across eleven everyday
diet topics, including 28 about water intake and hydration. Screening is provisional, not expert review.

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
03 / 08
02 / BUILD THE SEARCH
Find the words. Find the meaning.
Different retrieval methods solve different parts of the same search problem.
LEXICAL SEARCH
Exact terms and structure
TF-IDF and BM25 use an explicit index of words,
counts and positions. Section-aware BM25 can
give a match in results more weight than a
match in background text.
SEMANTIC SEARCH
Related wording
MiniLM turns each passage into a 384-number
vector. A question is encoded the same way, so
related wording can match even when the exact
words differ.
The index contains 115,883 semantic vectors from 102,752 source passages. Overlapping chunks fit the
256-token limit with zero truncated inputs; complete passages remain available for lexical search and
inspection.
HYBRID + RELEVANCE RANKING
Bring candidates together, then look again.
Reciprocal Rank Fusion combines lexical and semantic rankings. A MiniLM cross-encoder reranks up to
30 candidates using the query, title and bounded query-focused abstracts or source passages.
WHAT CAN BE INSPECTED
The search trace exposes the terms, expansions, scores, section weights, filters and corpus version. Quoted
phrases use token positions; the lexical methods also support AND, OR and NOT. Year, full-text and other filters
help narrow the search.
The reranker sees a selected passage, not the entire paper. Its score estimates relevance to the question; it does not
determine whether a scientific claim is true.

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
04 / 08
03 / USE THE PRODUCT
A search result you can open.
The interface carries the question through source inspection, comparison and paper summaries.
ACTUAL LOCAL INTERFACE  /  PHTHALO GREEN #123524
Everyday
A concise way to search and
open relevant evidence.
Dietitian
More study context and
side-by-side paper comparison.
Research
Retrieval traces, ranking and
summary diagnostics.
A result card shows the paper and evidence availability. Opening it reveals source passages and surrounding
sections. Readers can compare four papers, save investigations and export evidence. The optional Summarize
control reads 1-10 selected papers (default 3) and links answers to exact quotations.

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
05 / 08
04 / READ SELECTED PAPERS
Source-grounded summaries.
A local LLM reads selected papers and links its answer to source quotations.
OPTIONAL LOCAL READING STEP
Search ranks studies. The local model reads their stored
sections.
Choose 1-10 papers, default 3. Qwen3-4B-Instruct-2507 reads every stored passage in bounded groups
without changing retrieval rankings.
FROM SELECTED PAPERS TO A CHECKED ANSWER
01  PREPARE
Validate selected papers and fit source text to the model context.
02  EXTRACT
Keep candidate findings with exact quotations and source offsets.
03  CHECK APPLICABILITY
Consider exposure, outcome, population, dose, timing and comparator.
04  ANSWER OR ABSTAIN
Show a supported direct answer, or say selected evidence did not answer it.
LOCAL RUNTIME AND LIMITS
Q4_K_M model on Windows x64 Vulkan; 8,192-token context; one job at a time; idle unload after 120 seconds. Abstract-only
papers supply available text only. Applicability and support checks remain model judgments; exact citations do not guarantee
correct interpretation.

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
06 / 08
05 / TEST THE RETRIEVAL
What counts as a useful result?
Precision measures the proportion of retrieved papers that help address the question.
Precision@k = relevant papers in the first k / k
For example: eight relevant papers among the first ten gives Precision@10 = 80%.
We ran six everyday questions with hybrid plus relevance ranking and inspected the top ten papers for each.
Four query rewrites were also tried. Two matched BM25 searches provide a small baseline comparison. The
corpus and retrieval settings were kept fixed.
Grade
How the paper is treated
2 - relevant
Directly useful for part of the question; relevant null findings count too.
1 - related
Background, or a mismatch in food, preparation or outcome.
0 - off-topic
Does not address the exposure and outcome being searched.
Only grade 2 counts toward precision. Judgments use titles, abstracts and selected source sections. They were
made by AI, not an independent human panel; they assess retrieval relevance rather than study validity or
certainty.
A CONCRETE QUERY REFINEMENT
"Does eating salt raise blood pressure?" was rewritten as "Dietary sodium reduction blood pressure clinical trials".
Precision@10 rose from 60% to 80%, while Precision@3 fell from 100% to 66.7%. The added detail found more useful
papers overall but did not improve every rank.
The milk and egg rewrites were screened but not retained. All attempted queries and their review status are saved.

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
07 / 08
06 / READ THE RESULTS
Useful results, at three depths.
Five selected presentation examples using hybrid plus relevance ranking.
Query
P@3
P@5
P@10
Does coffee affect sleep?
100.0%
100.0%
90.0%
Is eating a late night meal bad?
100.0%
80.0%
80.0%
Does boiling vegetables remove vitamins?
66.7%
60.0%
80.0%
Dietary sodium reduction blood pressure clinical trials
66.7%
80.0%
80.0%
Does drinking milk help keep bones strong?
100.0%
80.0%
50.0%
Selected-example mean
86.7%
80.0%
76.0%
These examples were chosen after inspecting results. The original six-question set, including the weaker egg query,
averaged 88.9%, 76.7% and 63.3% at ranks 3, 5 and 10. The selected table is a demonstration, not a general accuracy
estimate.
SAME QUERIES, DIFFERENT METHOD
Two-query paired comparison
P@3
P@5
P@10
Flat BM25
100.0%
70.0%
75.0%
Hybrid + relevance ranking
83.3%
90.0%
85.0%
Pair: coffee/sleep and the refined sodium query. Hybrid did better at ranks 5 and 10; BM25 did better at rank 3. Two queries cannot
establish a general winner.

EvidenceAtlas
FOOD
CSD358  /  TRACK T6
FOOD QUESTIONS. SCIENTIFIC SOURCES.
08 / 08
07 / PROJECT AND REPRODUCIBILITY
A working system, with room to grow.
The project connects acquisition, full-text retrieval and source inspection in one local workflow.
WHAT IS WORKING
Search to comparison
Literature acquisition, structured passages,
lexical and semantic search, reranking, study
comparison, local LLM summaries and saved
investigations.
WHAT WAS CHECKED
Code and interface
77 focused regression tests and TypeScript
checking passed in the November 5 release
check. Dated browser and synthetic model
checks are recorded separately; no independent
summary accuracy benchmark is claimed.
The Track T6 contribution is the use of document structure throughout the workflow: sections influence
retrieval, passages link back to papers, and the reader can inspect how a result was found. The ranking
algorithms are established methods. The project work lies in combining them with food-specific acquisition and
an interface that keeps study context visible.
RUN AND REPRODUCE
python -m evidenceatlas.cli serve --port 8765
Run from the app folder with EAF_ROOT set to the data directory, then open http://127.0.0.1:8765/.
README.md includes full installation instructions.
python scripts/evaluate_report.py
The evaluation script recalculates historical retrieval scores from frozen rankings and labels. Papers, indexes,
models and caches stay on E:. The measured project uses about 4.1 GB; acquisition reserves 40 GB free and
supports further growth. Retrieval models run locally; the optional summary model uses a compatible GPU and
needs no paid inference API.
Next: improve coverage where relevant papers are missing, select better passages for reranking, and repeat the
evaluation with independent reviewers. A larger model alone will not fill gaps in the corpus.
AI assistance was used for implementation, documentation and relevance judgments. Team ownership and the course demo recording
still need to be supplied for submission.
