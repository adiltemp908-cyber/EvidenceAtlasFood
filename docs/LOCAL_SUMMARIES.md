## November 4: abstain when evidence does not directly answer the question

Pipeline `local-full-paper-summary-v9` selects findings only when their source quotations and study context directly address the question. The model checks the requested exposure, outcome and explicit population, dose, timing and comparator constraints. Related topics, missing required context and answers to only part of a question can produce an empty selection. Direct null results remain eligible.

The final verification separately requires citation support and direct applicability. If no direct findings are identified, the interface says so and retains related source quotations for inspection. It limits that statement to the selected papers and available text; it never concludes that no studies exist anywhere. A draft that fails support checks receives a separate insufficient-answer message. These model checks remain provisional, not validated scientific judgments.

The new pipeline invalidates completed answer caches from earlier versions; unchanged section readings remain reusable. Saved investigations retain their historical data, but their summaries must be regenerated before the interface presents them under the new behavior.

Hybrid + relevance reranking is selected when the project opens. Installations missing the reranker fall back to Hybrid; those missing the dense index fall back to section-aware BM25. Users can still choose another method.

Verification: 35 focused regression tests and TypeScript compilation passed. A headless browser confirmed the default and reload selection, an actual Hybrid + reranker search, the abstention display and capability fallbacks, with no JavaScript errors. Eight synthetic selection cases using the installed model passed after tightening the dose and multiple-outcome instructions. The final verifier suppressed the unrelated answer but incorrectly also marked its faithful quotation as unsupported; that diagnostic limitation is retained in [prompt checks](checks/summary-applicability-2026-11-04.json). Two [complete pipeline checks](checks/summary-live-2026-11-04.json) using synthetic source text and the real model produced a direct answer and an abstention as expected. These checks do not measure accuracy on real nutrition questions.

## Paper count and latency

The Papers input accepts 1–10, limited by available search results, and defaults to 3. It selects the first N ranked results. The answer records how many papers were actually read. Smaller selections take less reading work but cover less evidence; every stored section of each selected paper is still processed.

Completed identical answers are reused. Section readings can be reused when changing the paper count for the same question. Exact batch plans are now cached by source text, model/runtime and batching version, avoiding repeated tokenization across questions and paper-count changes. Source or tokenizer changes invalidate the plan. Initial GPU startup and new full-text readings still take time. The displayed duration is labelled as the original reading time, so reopening a cached answer is not confused with rerunning it.

[Count-control and cache checks](checks/summary-speed.json). These timings used already-cached section readings and are not cold-start benchmarks.

---

# Update: source context and audit repairs

Pipeline `local-full-paper-summary-v8` adds deterministic source-role checks before selecting findings. Titles, methods, table rows without unambiguous context, and primary-study background/discussion cannot serve as that study's result. Structured abstract labels and publication-type metadata help identify source roles; these are conservative heuristics, not expert adjudication. Reviews can synthesize prior studies, with review attribution preserved.

The answer step receives an exact outcome quotation plus up to three exact descriptive passages from the same primary study. These context quotations are inspectable in the interface and may supply participant/intervention details, not additional outcomes. Guards reject the audited absent-from-excerpt/absent-from-paper confusion, trial/review confusion, and dropped association or uncertainty wording. The small model can still omit relevant findings or misinterpret evidence; a passing check is not a guarantee of correctness.

Reading caches now match the complete extraction inputs, model/runtime and extraction prompt rather than depending on the entire corpus. Adding unrelated literature therefore does not force unchanged sections to be read again. Cache reuse is displayed beside elapsed time. One transient local timeout/connection failure is retried; computer sleep or persistent runtime failures can still interrupt a job.

[October 21 checks and development-query comparison](checks/audit-gap-repair.json). The original implementation measurements below are historical.

---

# Local answers from retrieved papers

Implemented October 21, 2026. Search first, then click **Summarize top 10 papers**. This is an optional reading step; ordinary search, MiniLM embeddings and reranking are unchanged.

## What the model reads

The requested paper IDs and corpus fingerprint are checked against the local collection. Every stored passage is passed through the reader in tokenizer-bounded groups. Long paragraphs overlap across group boundaries. Actual chat-template tokens are checked against the 8,192-token context window; overflow fails visibly instead of silently dropping text. Abstract-only records cannot supply unavailable full texts. Figures and text missing from the stored XML are not read.

Each group can yield up to three findings with exact quotations. Fabricated quotations are rejected. Up to six notes per paper are retained, with a round-robin selection across papers for the bounded answer input. Reading all passages does not mean all findings survive this compression. The model selects up to four findings, writes each answer paragraph from one exact excerpt, and checks the draft against that source. Adjacent table rows are deliberately excluded from this final step after a development run confused a duration with a dose. Missing details are omitted rather than inferred.

Exact offsets, source links, some quantities and species/outcome terms are checked in code. A second model pass checks support. Both extraction and verification can still miss errors, limitations or counterevidence. Citation correctness is not equivalent to interpretation accuracy. No independent human validation or summary-accuracy benchmark is claimed.

## Runtime and storage

- Model: Qwen3-4B-Instruct-2507, Q4_K_M, pinned Hugging Face revision `4edb920b6f14e3b9284d4502a6485103d72cde05`.
- Runtime: llama.cpp b11753, portable Windows x64 Vulkan build; NVIDIA device is discovered automatically.
- Context: 8,192 tokens; one summary job at a time; GPU unload after 120 seconds idle.
- Model and runtime: `EAF_ROOT/models/`; provenance: `data/manifests/model-summarizer.json`.
- Per-job request, progress, section-reading cache and answer: `data/summaries/`. These stay outside GitHub.
- Cache identity includes question, ordered paper IDs, corpus fingerprint, model/runtime hashes, prompt hash and pipeline version. The corpus is checked again before publishing an answer.
- Runtime is bound to loopback with a generated local authentication key. No paid API is used.

## Measured functional check

Question: “Does green tea lower cholesterol?” Using the current Hybrid + relevance ranking top ten, the reading covered **4 full texts and 6 abstracts**, **134,332 stored source characters**, and **20 section groups**. A fresh full-reading run took **167.9 seconds**. The final run reused those identical section extractions and regenerated/rechecked **2 answer paragraphs** in **11.4 seconds**. All 21 retained source quotations were checked against exact source offsets. These are functional measurements for one question, not a retrieval precision score or a scientific accuracy estimate. Machine load and source length affect timing.

Regression checks cover source offsets, complete passage coverage, context limits, stale-corpus rejection, cancellation, caching, unsupported-answer suppression, strict structured output and transient Windows file locks. Browser checks exercise the button, completed answer, source links and narrow-screen layout. Machine-readable results are in [checks/local-summary.json](checks/local-summary.json).

## Setup and troubleshooting

Run `python scripts/setup_summarizer.py` from the app folder using the same environment as the application, with `EAF_ROOT` set to your data volume. See the README for the complete application setup.

If the model cannot start, inspect `EAF_ROOT/tmp/local-summary-runtime.log`, close other GPU-heavy applications, and check your NVIDIA driver. This installer supplies Windows binaries; other operating systems need a compatible runtime and are not covered by this setup. `EAF_SUMMARY_PORT` changes the loopback port. Advanced users may override automatic device selection with `EAF_SUMMARY_DEVICE`, using a device reported by `llama-server.exe --list-devices`.

If reading stops, click summarize again to resume cached section readings. If the collection changed, run the search again first. An insufficient-answer message means no draft passed the checks; the interface still exposes the extracted source quotations. Longer or different-context models require separate testing before changing the pinned configuration.
