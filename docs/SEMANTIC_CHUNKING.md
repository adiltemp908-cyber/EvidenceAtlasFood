# Semantic passage splitting

MiniLM previously encoded only the first 256 model tokens of each source passage. In this collection, 7,000 passages exceeded that limit.

The semantic index now uses overlapping windows measured with the pinned MiniLM tokenizer. Each input fits within 256 tokens, including special tokens, with 32 source tokens of overlap. Boundaries use original character offsets: text is sliced from the source, never reconstructed or generated. Long words can change tokenization at a boundary, so each new window is checked again against the input limit.

- Source passages: 86,903, unchanged.
- Long passages split: 7,000.
- Semantic vectors: 98,131.
- Existing vectors reused exactly: 79,903.
- New vectors encoded: 18,228.
- Truncated semantic inputs: 0.

Paper IDs, passage IDs, full-text sections, lexical indexes and saved investigations are unchanged. Semantic search scores each paper by its best matching chunk, so several chunks from one paper do not take several result positions. Hybrid search preserves the matching span for split passages, and reranking receives that span rather than the start of the long paragraph. Search cards show the span; “Read in context” opens the original complete passage. Extraction and comparison still use source passages.

This applies to **Semantic** and **Hybrid** search. Pure keyword search is unchanged. No titles were added to embedding inputs, which allowed unchanged short-passage vectors to be reused. Future collection expansions retain the chunking scheme and reuse identical chunk inputs.

## Reproduction and rollback

After setup and lexical indexing, run `python -m evidenceatlas.cli dense-index` from the app directory. The command uses local model files, writes checkpoints on the configured data volume, and reuses a matching active passage index when available. It activates only after vector and corpus checks pass. Restart the app after updating its Python source.

Chunk settings and character offsets are recorded in the semantic index manifest. The live corpus fingerprint remains `10800e54e68ce1dbeb033daa23df662a30355a662c1b5a4fc44363a5c0905709`; the chunking version is `token-windows-v1`. The previous index remains on disk. For this migration, its pointer and the before/after searches are retained under `experiments/passage-splitting-v1` on the data volume. Restoring `previous-pointer.json` to `indexes/dense-active.json` rolls back semantic indexing without changing the papers.

## Checks and limits

30 focused tests passed, covering token boundaries, overlap, embedding reuse, subsequent expansion, source preservation, hybrid matching, reranker input and existing retrieval behavior. The interface compiled successfully. Live checks used the same six questions saved before the change, verified exact source excerpts, and preserved 19 saved investigations. See [verification counts](checks/passage-splitting-v1.json).

A separate deterministic diagnostic used 12 text excerpts from the ends of long passages as queries and checked whether their source paper appeared in the first 10 results: 11/12 before and 12/12 after. These are source-recovery probes, not independently judged nutrition questions, and cannot establish Precision@10 or overall accuracy. Historical benchmark results remain unchanged.

Window boundaries are token-based and can cut sentences; overlap and access to the original context reduce that limitation. Chunking does not establish study quality, applicability, or evidence stance. The reranker has its own input limit and remains experimental.
