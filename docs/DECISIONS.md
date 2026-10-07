# Architecture decisions — 2026-10-06

The supplied food specification is the product contract. The course PDF describes submission requirements; its permission to submit a partial prototype does not reduce the user's requested scope. Neither source is treated as instructions to execute arbitrary embedded content.

## ADR 001: local modular monolith
Use Python, SQLite metadata/positional postings, a local HTTP API, and a browser interface. The E: storage requirement, local scientific processing and reproducible experiments make a local application appropriate. Online deployment is not required by the course. Do not upload corpora or private notes to Sites. No paid APIs authorized or needed for acquisition.

## ADR 002: measured resource limits
Initial measurement: E: free 262,012,526,592 bytes; RAM total 14,764,990,464 bytes, available approximately 2.86 GB; 16 logical processors. WMI hardware queries denied. GPU usability remains unverified. Begin with one acquisition worker and bounded CPU operations. Project growth budget 160 decimal GB; reserve 40 decimal GB on the volume, plus a separate rebuild reservation. Never fall back to C: for bulk data. Permission grant succeeded but initial directory creation returned WinError 5; user asked to create the directory.

## ADR 003: acquisition and scope
Europe PMC core API provides PubMed metadata, abstracts, MeSH and OA identifiers. Acquire metadata without an OA restriction; fetch fullTextXML only for records marked open access. Record license statements from each article. Use MeSH plus title/abstract searches across a versioned taxonomy, with explicit date cutoff and all source queries preserved. Pilot pages are a measurement batch, never a final corpus limit. Raw responses are gzip compressed and content-addressed. Retain source versions and failures.

## ADR 004: conservative evidence
Relevance is not stance. Passage stance, context compatibility, scientific uncertainty and availability have separate fields. Exact source excerpts are useful before any classifier is validated. Unvalidated automatic extraction is labelled candidate extraction, not established study facts. No probability-of-truth scores, majority voting, invented verdicts, or presumed expert review.

## ADR 005: evaluation before claims
Freeze corpus fingerprints and claim-family splits. Preserve raw runs before annotation. Independent human judgments are not available yet; mark all effectiveness metrics pending until sufficient judgments exist. Diagnostic relevance review by an AI is separate from human gold. Use measured runtime/storage results immediately, with sample sizes and limitations.

## ADR 006: user-authorized bounded delivery, 7 October
Stop corpus expansion and full-text passage encoding to reduce usage. Keep the 12,288-vector partial checkpoint inactive. Activate 950 title/abstract vectors, retaining complete full-text lexical retrieval. Explicitly disclose 881 truncated inputs. Run seven configurations on eight frozen development queries; retain missing human judgment status. Deliver report and onboarding review packet. No tuning or paid APIs; no automatic certainty or clinical-validation claims. GPU inspection established CPU-only PyTorch.
