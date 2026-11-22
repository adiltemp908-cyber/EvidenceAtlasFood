# Known limitations

## Retrieval evaluation

On November 15, all 310 distinct question–paper pairs pooled from six methods were reviewed. Hybrid + reranker averaged 74% Precision@10 and 0.871 nDCG@10. The ten questions cover a small set of topics. Pool-relative recall measures coverage of relevant papers returned by the participating methods. [Results, grades and scope](../evaluation/pdf-easy-medium-10-2026-11-15/RESULTS.md)

## Study context and summaries

A relevant passage can describe another population, intervention or study arm. Extracted doses and timing remain candidate mentions until the reader verifies their attribution. The summary model checks quotations and may abstain when it finds no directly applicable evidence. The retrieval scores do not measure summary accuracy. [Summary behavior and checks](LOCAL_SUMMARIES.md)

## Collection coverage

Open-access availability determines whether the reader sees a full text or an abstract. Shared cohorts, primary studies included in reviews, and incomplete correction or retraction metadata can affect interpretation. [Collection and screening](COVERAGE_2026_11_04.md)
