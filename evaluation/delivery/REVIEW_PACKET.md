# Independent review packet

`review-packet.json` contains 49 real claim-paper pairs for four declarative development claims, blinded to retrieving method/rank. It is a manageable onboarding subset, drawn from the union of each method's top three. It is not a complete judgment set and cannot establish full-pool recall or held-out performance. All judgments start blank.

For each item, read the claim and open the source/context URL. Read methods, results and limitations; candidate passages alone may misattribute a review or background finding. Local source URLs refer to the running collection: verify its corpus fingerprint equals the packet's fingerprint. The frozen source is `E:\EvidenceAtlasFood\experiments\delivery-v1\corpus.sqlite` if the running collection later changes.

Fill the item's `judgment` object with your actual reviewer ID, `reviewer_kind: "human"`, qualifications, relevance (0-3), stance (`supports`, `contradicts`, or `insufficient to establish`), and compatibility (`matches`, `differs`, or `unknown`). Follow `../ANNOTATION_GUIDE.md` and `../PROTOCOL.md`. Model suggestions must use a separate AI record. No expertise is presumed.

For a direct-evidence relevance grade (2 or 3), add at least one rationale object containing `paper_id`, `passage_id`, `start`, `end`, and `quote`. Offsets are zero-based within that passage, end exclusive; the validator requires an exact substring match. Candidate passage offsets describe the whole passage and are not preselected rationale labels. Select the actual supporting span yourself.

Save completed **judgment objects only**, one JSON object per line, as `judgments.jsonl` on E:. Do not include blank/incomplete objects or silently fill missing labels with zero. Preserve independent reviewers' files; adjudicate disagreements explicitly before evaluating.

```powershell
python -m evidenceatlas.judgments E:\EvidenceAtlasFood\experiments\delivery-v1 E:\EvidenceAtlasFood\experiments\delivery-v1\judgments.jsonl --reviewer-kind human
```

Missing top-k labels keep precision/nDCG unavailable. Complete the larger `blinded-pool.json` for the full development pool; keep held-out families separate. This packet does not resolve domain-screening validity, stance accuracy, context extraction, scientific certainty or comprehension testing by itself.
