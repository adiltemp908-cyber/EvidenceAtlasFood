# EvidenceAtlas Food

EvidenceAtlas Food



## EvidenceAtlas Food

From a food question to the studies behind it.

A working search and comparison tool for everyday readers, dietitians and researchers.

Find nutrition papers in PubMed and Europe PMC.

Separate abstracts, methods, results and other sections.

Match exact terms and meaning, then rank candidate papers.

Open source passages, compare studies and save an investigation.

Review ranked papers and calculate Precision@3, @5 and @10.

Start with the literature.

The collection was built from scientific records, then turned into searchable sections.

## Start with the literature.

We searched by scientific subject headings and by words in titles and abstracts. The topic plan covered foods, nutrients, meal timing and preparation: for example caffeine and sleep, sodium and blood pressure, and cooking and vitamin retention.

When an open-access full text was available, the JATS XML was downloaded and parsed. Each passage keeps its parent paper, section name and position. This lets a result open at the relevant evidence while the reader checks the surrounding methods or discussion.

More than the abstract

494 records contain ingested full text. Methods, results, discussion and tables can be inspected where the source supplies them.

A visible limit

473 records have abstracts only; six contain metadata only. These availability labels stay visible rather than implying a complete paper was read.

Raw responses and content hashes are retained. The first 77-record pilot included 42 full texts and informed later collection growth.

Find the words. Find the meaning.

Different retrieval methods solve different parts of the same search problem.

## Find the words. Find the meaning.

Exact terms and structure

TF-IDF and BM25 use an explicit index of words, counts and positions. Section-aware BM25 can give a match in results more weight than a match in background text.

Related wording

MiniLM turns each passage into a 384-number vector. A question is encoded the same way, so related wording can match even when the exact words differ.

All 37,975 passage vectors are complete. The model reads up to 256 tokens per passage; 2,723 longer passages were truncated for encoding. Their complete text is still stored and searchable through the lexical index.

Bring candidates together, then look again.

Reciprocal Rank Fusion combines lexical and semantic rankings. A MiniLM cross-encoder then reorders up to 20 candidates using the question, paper title and a selected passage.

The search trace exposes the terms, expansions, scores, section weights, filters and corpus version. Quoted phrases use token positions; the lexical methods also support AND, OR and NOT. Year, full-text and other filters help narrow the search.

The reranker sees a selected passage, not the entire paper. Its score estimates relevance to the question; it does not determine whether a scientific claim is true.

A search result you can open.

The interface carries the question through to source inspection and study comparison.

## A search result you can open.

A concise way to search and open relevant evidence.

More study context and side-by-side paper comparison.

Retrieval traces and experimental model diagnostics.

A result card shows the paper and evidence availability. Opening it reveals source passages and surrounding sections. Readers can compare up to four papers, save notes with an investigation, and export evidence for later use.

What counts as a useful result?

Precision measures the proportion of retrieved papers that help address the question.

## What counts as a useful result?

For example: eight relevant papers among the first ten gives Precision@10 = 80%.

We ran six everyday questions with hybrid plus relevance ranking and inspected the top ten papers for each. Four query rewrites were also tried. Two matched BM25 searches provide a small baseline comparison. The corpus and retrieval settings were kept fixed.

| Grade | How the paper is treated |
| --- | --- |
| 2 - relevant | Directly useful for part of the question; relevant null findings count too. |
| 1 - related | Background, or a mismatch in food, preparation or outcome. |
| 0 - off-topic | Does not address the exposure and outcome being searched. |

Only grade 2 counts toward precision. Judgments use titles, abstracts and selected source sections. They were made by AI, not an independent human panel; they assess retrieval relevance rather than study validity or certainty.

"Does eating salt raise blood pressure?" was rewritten as "Dietary sodium reduction blood pressure clinical trials". Precision@10 rose from 60% to 80%, while Precision@3 fell from 100% to 66.7%. The added detail found more useful papers overall but did not improve every rank.

The milk and egg rewrites were screened but not retained. All attempted queries and their review status are saved.

Useful results, at three depths.

Five selected presentation examples using hybrid plus relevance ranking.

## Useful results, at three depths.

| Query | P@3 | P@5 | P@10 |
| --- | --- | --- | --- |
| Does coffee affect sleep? | 100.0% | 100.0% | 90.0% |
| Is eating a late night meal bad? | 100.0% | 80.0% | 80.0% |
| Does boiling vegetables remove vitamins? | 66.7% | 60.0% | 80.0% |
| Dietary sodium reduction blood pressure clinical trials | 66.7% | 80.0% | 80.0% |
| Does drinking milk help keep bones strong? | 100.0% | 80.0% | 50.0% |

Selected-example mean

These examples were chosen after inspecting results. The original six-question set, including the weaker egg query, averaged 88.9%, 76.7% and 63.3% at ranks 3, 5 and 10. The selected table is a demonstration, not a general accuracy estimate.

| Two-query paired comparison | P@3 | P@5 | P@10 |
| --- | --- | --- | --- |
| Flat BM25 | 100.0% | 70.0% | 75.0% |
| Hybrid + relevance ranking | 83.3% | 90.0% | 85.0% |

Pair: coffee/sleep and the refined sodium query. Hybrid did better at ranks 5 and 10; BM25 did better at rank 3. Two queries cannot establish a general winner.

A working system, with room to grow.

The project connects acquisition, full-text retrieval and source inspection in one local workflow.

## A working system, with room to grow.

Search to comparison

Real literature ingestion, section and positional indexes, passage embeddings, hybrid retrieval, reranking, source navigation and saved investigations.

Code and interface

23 core/dense tests and the TypeScript check passed in the delivery check. Earlier browser checks exercised search, source viewing, comparison, saving and export.

The Track T6 contribution is the use of document structure throughout the workflow: sections influence retrieval, passages link back to papers, and the reader can inspect how a result was found. The ranking algorithms are established methods. The project work lies in combining them with food-specific acquisition and an interface that keeps study context visible.

Run from the app folder with EAF_ROOT set to the data directory, then open http://127.0.0.1:8765/. README.md includes full installation instructions.

The evaluation script recalculates every reported score from saved rankings and labels. Papers, indexes, models and caches stay on E:. The measured project uses about 4.1 GB; acquisition reserves 40 GB free and supports further growth. Models run locally on CPU without a paid inference API.

Next: improve coverage where relevant papers are missing, select better passages for reranking, and repeat the evaluation with independent reviewers. A larger model alone will not fill gaps in the corpus.

AI assistance was used for implementation, documentation and relevance judgments. Team ownership and the course demo recording still need to be supplied for submission.
