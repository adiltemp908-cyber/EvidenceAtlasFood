# Related work and contribution boundaries

- Wadden et al., [Fact or Fiction: Verifying Scientific Claims](https://aclanthology.org/2020.emnlp-main.609/) (EMNLP 2020), introduces evidence retrieval, scientific claim labels and rationale selection using abstracts. EvidenceAtlas adopts this separation but requires food-specific full texts and context. SciFact is not food-domain validation.
- Wadden et al., [SciFact-Open](https://arxiv.org/abs/2210.13777) (2022), motivates open-corpus retrieval and pooled assessment. Our benchmark must report the scope of judged evidence and avoid treating unjudged papers as irrelevant.
- Cormack, Clarke and Buettcher, [Reciprocal Rank Fusion](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf) (SIGIR 2009), supplies the fusion method. Combining lexical and dense ranking is established practice, not novelty by itself.
- [Elicit Systematic Review](https://elicit.com/blog/systematic-review/) already supports search, screening and full-text extraction workflows. A comparison table or citations alone are not a new contribution.

The project's testable contribution is preserving food exposure/context and targeting alternative findings while keeping passage stance separate from applicability and uncertainty. Whether this improves recovery or reduces misleading assessments remains an empirical hypothesis. No improvement or novelty beyond that scoped hypothesis has been established.
