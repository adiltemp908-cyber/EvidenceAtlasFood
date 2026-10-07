# Primary sources checked

Checked 2026-10-06. Live responses and observed failures are distinguished from documented capabilities.

- [PubMed search help](https://pubmed.ncbi.nlm.nih.gov/help/): field-tagged MeSH and title/abstract queries; indexing-dependent filters can miss recently unindexed records. Search API probes succeeded.
- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/): documentation page encountered a browser challenge in this session. ESearch itself succeeded. Acquisition is throttled to at most one request per second, below the usual unauthenticated ceiling, and honors retry delays.
- [Europe PMC REST service](https://europepmc.org/RestfulWebService): core metadata, cursor paging, fullTextXML. Documentation search results available; some direct page fetches timed out/returned challenges. Actual `/fields`, `/search` and `/{PMCID}/fullTextXML` probes succeeded against the EMBL-EBI service.
- [Europe PMC open access](https://europepmc.org/downloads/openaccess): OA content is available through designated bulk/services; article license terms vary. Preserve each license and do not equate free visibility with redistribution permission.
- [PMC developer policy](https://pmc.ncbi.nlm.nih.gov/tools/developers/): use approved programmatic services and article-specific reuse conditions. No website scraping or paywall bypass is used.
- [Sentence Transformers model documentation](https://sbert.net/docs/sentence_transformer/pretrained_models.html): small MiniLM models are candidates for CPU retrieval; general benchmark performance does not establish nutrition-domain quality.
- [all-MiniLM-L6-v2 model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2): candidate model, not a food-domain-validated choice. Pin actual revision when installed.
- [SQLite documentation](https://www.sqlite.org/fts5.html): consulted for out-of-core lexical infrastructure; the current inspectable baseline uses explicit SQL postings and Python TF-IDF/BM25 calculations rather than delegating ranking to FTS5.

No novelty claim is made merely for hybrid search, citation display or scientific summarization. Related-work review and comparative experiments remain required before claiming a new contribution.
