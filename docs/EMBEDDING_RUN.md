# Full-text passage embedding continuation

The user explicitly authorized resuming embeddings after the reduced delivery. Corpus expansion is not run concurrently because it would invalidate the frozen index build.

The saved checkpoint contains 12,288 of 37,975 passage vectors for corpus `eb8022c2e62857317677b2b1b7fb42f40c62777435a0ddada3b3ca6d565534df`. Resume uses the same pinned all-MiniLM-L6-v2 PyTorch CPU model and normalized float32 vectors. The separately tested quantized ONNX model is not mixed into this checkpoint.

Bulk storage was rechecked: 258.6 GB free on E:, successful write/delete probe in E:/EvidenceAtlasFood/tmp. Available RAM was about 2.6 GB. CPU uses four PyTorch threads; batch size 32. A 96-passage timing check found similar times for batches of 16 and 32, so the existing batch size was retained.

Progress is checkpointed every 512 passages in `E:/EvidenceAtlasFood/indexes/dense-eb8022c2e6285731/progress.json`. This records encoded count, truncation count, resume offset and elapsed time for the current invocation. If interrupted, at most the work since the last checkpoint is repeated. Logs are in `E:/EvidenceAtlasFood/tmp/dense-resume.log` and `dense-resume.stderr.log`; PowerShell may buffer the console log, so the progress JSON is authoritative during execution.

Before activation, every vector must be finite, have the expected shape and unit norm, and match the unchanged corpus fingerprint. The original 950-vector paper index remains available. Use `python -m evidenceatlas.cli dense-activate --level paper` for rollback or `--level passage` for the completed section-passage index. Each switch validates the target; an incomplete checkpoint cannot be activated. Restart the server once to load the new code; subsequent searches notice pointer changes automatically.

Embedding input is the first 256 model tokens of each normalized passage. Truncation remains explicit; lexical retrieval and source inspection retain complete paragraphs. Passage embeddings improve the representation available for retrieval but do not establish stance, context compatibility or accuracy.

The follow-up experiment uses the same eight development questions, same corpus and seven configurations. New rankings are stored separately from `delivery-v1`; old AI labels remain tied to the paper-index audit and are not treated as labels for unseen passage-index results. Rank overlap and latency are descriptive, not proof of improvement. Context matching remains deferred.

## Completed outcome
37,975 / 37,975 vectors are complete and active; 25,687 new vectors were computed after resuming. The resumed invocation took 805.08 seconds, excluding the earlier checkpoint work. All vectors passed finite/shape/unit-norm checks. There are 2,723 truncated passage inputs (7.17%); full normalized text is still retained. Rollback to the paper index was validated and the passage index restored.

The passage-v1 experiment is complete: all four lexical configurations preserved their top-10 rankings; dense, hybrid and reranked-hybrid order changed on all eight queries. Mean shared top-10 papers were 3.75, 6.625 and 7.375 respectively. No improvement claim follows from rank changes. Exact source links, filters and browser passage retrieval passed integration checks. No model build remains running.
