# Course demo plan (not a recording)

The supplied PDF requires a 5–8 minute prerecorded live demo with no slides. This script is preparation only; no video has been recorded or uploaded.

1. **0:00–0:45 — problem and T6.** Open the working app. Explain a food claim's dependence on dose, timing, population and comparison. Show the local collection count and abstract/full-text distinction.
2. **0:45–2:00 — real investigation.** Search caffeine and sleep, open a source excerpt in its full-text section, inspect surrounding limitations. Show at least one limitation, such as a review/background passage ranking above direct evidence.
3. **2:00–3:00 — compare context.** Switch to Dietitian, select two studies, open candidate dose/population mentions. Explain why context compatibility and stance are separate, and why unknowns remain visible.
4. **3:00–4:30 — substantive IR.** Switch to Research. Show original/expanded query, token contributions, BM25 parameters and section weights. Run a phrase/Boolean query. Open `retrieval.py` and inspect actual SQL postings rather than only a screen.
5. **4:30–5:30 — experiments.** Show frozen run artifacts and actual latency/storage measurements. If human judgments remain unavailable, state this clearly and show the annotation protocol; do not present missing P@k/F1 as completed evaluation.
6. **5:30–6:30 — model limits and persistence.** If verified, show dense/hybrid rank changes and an experimental stance failure. Save an investigation, reload notes and export citations/evidence with scope preserved.
7. **6:30–7:30 — ownership and next steps.** Each real team member explains the component they actually own. Disclose AI-generated code/documentation and actual human work. Do not use invented roles.

Recording readiness still depends on frozen experiment review and team ownership details. Course report must stay within eight pages excluding references/appendix.

## Updated evaluation demonstration
In Collection & evaluation, expand Preliminary AI relevance audit: 8/12 direct or near-direct results, only 2/12 judged directly applicable. State that the annotator was AI and also built the system; these are not validated accuracy scores. Show the population mismatch case and explain why compatibility remains unknown. Run `python -m evidenceatlas.audit E:\EvidenceAtlasFood\experiments\delivery-v1` to demonstrate reproducible source-span validation without model inference. Keep the entire recording within the original 5-8 minute limit.

## Full-text semantic continuation
Semantic search now uses 37,975 passage vectors. Show the active index and its 2,723 truncated inputs. The original 12-pair AI audit is explicitly historical. Compare lexical and semantic results and open the actual matched passage; show passage-v1 artifacts without claiming accuracy improvement. Encoding is already complete; do not start a build during the recording.
