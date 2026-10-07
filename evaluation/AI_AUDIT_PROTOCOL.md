# Bounded AI relevance audit - 7 October 2026

Purpose: measure a small, explicitly provisional retrieval diagnostic without waiting for human reviewers. This does not validate the AI annotator, the NLI model or the science of the claims.

Selection fixed before labeling: top three papers from the already frozen `hybrid_rerank` run for each declarative development claim (food-002, 004, 006, 008). Twelve claim-paper pairs; four topic families; no held-out queries used. Records were shuffled with seed 20261007 and rank scores omitted from the reading packet. The annotator knows the selected method, so this is **not fully blinded**. No favorable-result replacement or model tuning is allowed during this audit.

Annotator: Codex assistant, AI, no clinical credentials or independent reviewer. This assistant also implemented the system; self-evaluation bias is a material limitation. Labels follow the existing PROTOCOL.md relevance scale: 0 unrelated; 1 related/background; 2 directly relevant but applicability differs or is unclear; 3 direct applicable evidence. Reviews can contain direct discussion, but they are secondary evidence and cannot be counted as independent primary studies.

Read the full abstract and the selected passages, with targeted source-context checks when needed. This is a bounded source-reading audit, not a complete systematic appraisal of every full text. Record exact source spans, rationale, availability, review limitations, stance and compatibility separately. Absence from the inspected excerpts does not establish absence from the paper. A nonsignificant result is not automatically contradiction. Population/exposure/outcome mismatch must remain explicit.

Primary metric: macro P@3 using grade >=2, meaning direct or near-direct retrieval relevance, **not claim correctness**. Also report the grade distribution and grade-3-only fraction to expose applicability limits. Sampled retrieval ranks are complete at k=3, so no unjudged top-three result is silently scored zero. Do not publish recall, nDCG, stance F1 or an overall accuracy percentage from this selected, small pool. Exact-span validation is a mechanical integrity check, not evidence of scientific support.

Save AI labels separately from human judgments. Independent reviewers remain necessary for a defensible final benchmark; this audit can guide review and expose failures in the meantime.
