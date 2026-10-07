# Milestone 1: measured feasibility

Completed acceptance checks on 2026-10-06, with screening validation still provisional.

## Environment and access
- Read the full food specification and all eight course PDF pages; visually checked pages 6–7.
- Empty initial workspace. Code/docs under this `outputs/EvidenceAtlasFood` project.
- E: initially had 262,012,526,592 free bytes. Folder creation initially failed; user created it, session permission was renewed, and an actual write probe succeeded.
- 16 logical CPUs, 14.76 GB physical RAM. Available memory fluctuated between roughly 1.1 and 2.9 GB during checks. No assumption of usable GPU or paid service access.
- Public Europe PMC search/core/fullTextXML and NCBI PubMed ESearch returned successful actual responses.

## Pilot
`pilot-persistent.json` is the measured run artifact. Batch: one page of ten records for each of two discovery routes over four topics. It is a sampling setting, not a final paper cap.

| Measurement | Observed |
|---|---:|
| Unique records | 77 |
| Verified full texts | 42 |
| Abstract-only records | 35 |
| Parsed passages | 3,629 |
| Acquisition/parse elapsed | 100.52 seconds |
| HTTP requests | 54 |
| Response bytes | 7,889,250 |
| SQLite logical bytes with explicit indexes | 66,818,048 |
| Project bytes during run (including WAL/temp/logs) | 123,994,458 |
| Process RSS after indexing/report serialization | 140,083,200 |
| Recorded full-text failures | 0 |

RSS is an observation, not a continuously sampled peak. The storage measurement includes temporary SQLite WAL growth and cannot be extrapolated as a final optimized index size.

## Real retrieval
Twelve saved runs (four queries × TF-IDF, BM25, section-aware BM25) rank our own ingested collection. The query `caffeine sleep dose timing` retrieves source paragraphs including PMID 42026645, *Caffeine intake from different dietary sources and its association with sleep quality in employed adults*, with a results section and a conclusion noting timing/objective-measurement limitations. This demonstrates source retrieval, not a validated claim assessment.

Observed failure: a review/discussion on energy drinks can outrank a primary study's results. A small recent-record sample also retrieves loosely related material on some queries. Section weights remain hypotheses, not proven improvements. Model judgments and human relevance metrics have not been fabricated.

## Screening and query correction
The first RAM-only probe (`pilot-transient.json`) discovered an unsupported `MESH_HEADING` field and overly broad protein terminology. That artifact is retained as a failed design diagnostic. Europe PMC `/fields` confirmed the field is unavailable. Taxonomy v2 uses real PubMed MeSH ESearch plus Europe PMC title/abstract search, and narrows dietary protein and sodium expressions. PubMed query translations and raw content hashes are available in E: manifests.

The persistent pilot has 79 accepted and one needs-review **discovery decisions**, not 80 unique papers. These are provisional deterministic screens. Independent human screening is still required; no false-positive/negative rate is claimed.

## Scaling estimate and decision
Naive pilot arithmetic is roughly 0.87 MB of logical SQLite per unique record and 1.61 MB/record including temporary project footprint. A 10,000-record collection would be approximately 8.7–16.1 GB under those assumptions; this is a rough projection, not a promise, and topic/full-text mix changes it. Positional JSON postings and duplicated paragraph context are measurable overheads to optimize before very large expansion.

At 384 float32 dimensions, raw dense vectors cost 1,536 bytes/passage, about 5.6 MB for this pilot before model/index overhead. Dense encoding latency and actual model memory must be measured before choosing corpus-scale settings.

Continue topic-balanced metadata-first expansion, conserve the 160 GB project budget and 40 GB free-space reserve, measure batches, and reserve rebuild space. Prefer bounded CPU inference and SQLite to distributed infrastructure. PubMed's 9,999 search-ID boundary must be handled by date partitions before crossing it; never silently truncate it.
