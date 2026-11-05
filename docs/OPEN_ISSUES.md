# Open issues and continuation order

The user authorized continuing independent work while deferring the newly identified context-matching issue. The reduced resource scope remains in force. These issues are unresolved, not silently waived.

## Context matching - partially addressed, validation outstanding
The November 4 summary pipeline adds direct-applicability selection and verification with abstention, but these are model-assessed checks, not validated study-context matching. The historical 12-pair AI audit found retrieved papers with different populations, timing, exposures and outcomes. Relevance scores are not applicability or certainty. Current behavior keeps compatibility unknown, extraction marked as candidate mentions, and claim-level assessment pending. Continue implementation/evaluation tooling; do not promote this build as an authoritative automatic food fact checker.

When resumed: freeze the current baseline, define population/exposure/timing/comparator constraints, and compare changes against identical queries and evidence budgets. Separate explicit mismatch from missing context, retain counterevidence, and validate study-arm attribution before using it for exclusion. Do not simply remove all papers that lack a context term. Use new reviewed data for evaluation; the 12 audited pairs are now development examples, not an independent final test.

## Scientific evaluation - external review needed
AI labels can support provisional diagnostics. They cannot establish independent domain validity. Obtain real relevance/stance/context judgments and adjudication; then compute supported metrics. Held-out claim families remain unused for tuning. Screening validation, citation support, overlapping cohorts and comprehension studies remain outstanding.

## Resource-intensive scope - deferred
The user subsequently authorized further acquisition: the October 13 collection expansion and incremental embeddings are complete; see COLLECTION_CONTINUATION.md. Further batches remain possible. Training/tuning, exhaustive ablations, complete refresh and public deployment remain deferred. The user subsequently authorized resuming full-text dense encoding; it has completed from the retained checkpoint, with 115,883 chunk vectors active as of November 4. The original 37,975-vector snapshot remains historical. Context matching remains a separate open issue.

## Submission - real user/team inputs
The published repository identifies Adil Muhammed (2410110018) and links an existing demo. The November 5 update preserves both. Review the updated report and confirm that the linked recording meets the required 5-8 minute live-demo format and current feature scope before course submission. The recording content and submission status were not verified in this update.

## Resumed work completed
The audit now has a repeatable validation command; application evaluation separates AI diagnostics from human judgments; the report includes the actual limited audit; source packaging excludes models, corpus, private sessions and caches.
