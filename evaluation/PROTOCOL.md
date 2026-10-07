# Evaluation protocol v1

Use a versioned food claim set stratified by topic, everyday/technical wording, ambiguity, qualified doses/timing/populations, null findings, substitution, animal-human extrapolation and missing evidence. Split by claim family, not individual paraphrase. Freeze corpus, parser, tokenizer, index, model revisions, query config and random seeds before held-out evaluation.

Pool the union of top 20 unique papers from flat TF-IDF, BM25, structure-aware lexical, dense, hybrid, reranked hybrid and full-system ablations. Blind reviewers to run identity. Record reviewer ID/qualification, independent decisions, exact evidence offsets, disagreements and adjudication. Do not treat AI suggestions as human gold. Expert review and comprehension participants are currently unavailable.

Relevance grades: 0 unrelated, 1 related/background, 2 direct but materially different/unclear applicability, 3 direct applicable evidence. Relevance is distinct from supports/contradicts/insufficient stance. Annotate applicability per population/exposure/dose/timing/preparation/comparator/outcome, with unknown retained.

Report P@k with grade >=2 as relevant; report judged fraction separately and do not silently score unjudged as irrelevant. With incomplete top-k judgments, P@k is unavailable and bounds may be reported. Recall denominator is all relevant documents in the frozen judged pool, never all scientific truth. nDCG uses gains 2^grade-1 and is reported only under a stated complete judgment protocol. Deduplicate parent papers before metrics.

Counterevidence recall applies only to claims with judged applicable counterevidence. Stance macro-F1/confusion/rationale accuracy require reliable labels. Context extraction errors are separate from compatibility errors. Oracle-evidence and end-to-end results are distinct. Report citation support, unsupported statements, abstention/coverage and readability; no calibration without validation.

Required runs: TF-IDF; BM25; zone lexical; dense; hybrid ± rerank; full system minus normalization/context/counterevidence individually; generic retrieved summary versus domain-aware assessment with equal evidence/inference budgets where feasible. Unimplemented runs must be reported unavailable, not copied from a baseline.

Analyze negation, identity ambiguity, dietary substitution, nonsignificance, surrogate outcomes, population mismatch, overlap and OA selection. Report unfavorable results with sample sizes. Save queries, run scores/ranks, qrels, annotation source spans, configs and corpus/model versions outside searchable article text.
