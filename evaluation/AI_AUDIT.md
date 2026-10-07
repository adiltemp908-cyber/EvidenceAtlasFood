# Preliminary AI retrieval audit - 7 October 2026

**I can measure provisional relevance using AI labels. I cannot turn self-assessment into independent validation.** This audit reads real source material and preserves every label, rationale and source offset.

The fixed sample contains the top three reranked-hybrid papers for each of four declarative development claims: caffeine/sleep timing, protein/CKD safety, sodium/BP-response variation and TRE/glucose independent of weight loss. There are 12 pairs: nine full-text records and three abstract-only records. Review consisted of abstracts, selected passages and targeted context checks, not exhaustive appraisal of each full text.

| Result | Observed value |
|---|---:|
| Direct or near-direct relevance (grades 2-3), P@3 | 8/12 = 66.7% |
| Direct applicable evidence (grade 3) | 2/12 = 16.7% |
| Relevant but applicability differs/unclear (grade 2) | 6/12 |
| Related/background only (grade 1) | 4/12 |
| Unrelated (grade 0) | 0/12 |
| Exact rationale spans mechanically validated | 12/12 |

Both grade-3 results were review discussions. They are not two independently validated primary findings. Grade 2 includes a materially different population, timing or other qualifier: 66.7% is **not** a claim-correctness score. The grade-3 fraction is also an AI judgment, not a reliability guarantee.

The most useful failure is context mismatch. PMID 42289790 concerns high-protein diets in adults **without** CKD but was retrieved for a claim about people **with** CKD. PMID 42444712 concerns observational caffeine associations within eight hours, rather than a causal six-hour trial. PMID 42413885 studies a low-protein formula within low-protein counseling, rather than universal high-protein safety. These are retrieval/qualification diagnostics, not medical recommendations.

Limitations: 12 nonrandom results, four development families, one method, one AI annotator who also built the system, no independent adjudication, and partial source reading. The records were shuffled and ranking scores hidden during reading, but method identity was known. No held-out generalization, recall, stance F1, citation entailment accuracy or overall system accuracy is established. No parameter tuning followed this audit.

Artifacts: `delivery/ai-judgments.jsonl`, `delivery/ai-audit-notes.json`, `delivery/ai-audit-summary.json`; selection/rubric: `AI_AUDIT_PROTOCOL.md`. Human labels remain separate and absent. The PDF report and application evaluation page now include this limited AI audit. Reproduce it with `python -m evidenceatlas.audit E:\EvidenceAtlasFood\experiments\delivery-v1`; this validates the fixed sample and all saved source spans without new inference.
