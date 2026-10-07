# Screening diagnostic, 2026-10-06

This is an **AI inspection**, not independent human gold. A seed-42 sample of ten accepted records plus the first eight unresolved records was read during expansion. The input collection was still growing; this is diagnostic rather than a frozen performance estimate. No sensitivity/specificity percentage is asserted.

## Findings

| PMID | Existing screen | Diagnostic |
|---|---|---|
| 42654252 | Accepted | Plant-based dietary pattern review; relevant but not independent confirmation of included studies. |
| 40939275 | Accepted | Pediatric sweetener/BP cohort; relevant, pediatric context is essential. |
| 25117997 | Accepted | Cooked vitamin-D-enriched mushrooms in deficient prediabetic adults; relevant preparation/dose/population case. |
| 42797002 | Accepted | Adolescent plant-based diet review; relevant with developmental qualifications. |
| 41957112 | Accepted | Isolated seed-oil fraction tested for anticancer drug-like activity in cells/mice. Nutrition applicability is questionable; needs substantive scope review. |
| 41832741 | Accepted | Dietary fibre in immunotherapy patients; relevant but not general healthy-adult evidence. |
| 41736157 | Accepted | Dietary oil feeding experiment in rats; relevant mechanistic evidence, never a demonstrated human effect. |
| 41228536 | Accepted | Salt/atherosclerosis narrative review; relevant but not an independent clinical trial. |
| 42796929 | Accepted | Energy-drink/sleep narrative review; relevant, includes background claims and proposed future studies. |
| 40807542 | Accepted | Coffee fermentation/flavour technology; human sleep is mainly background. Likely overly permissive nutrition-health screening. |
| 40011815 | Needs review | Oral protein supplement clinical trial in hemodialysis; likely missed by limited outcome vocabulary. |
| 41334329 | Needs review | Coffee-use-disorder instrument with insomnia outcomes; potentially eligible indirect evidence. |
| 41516153 | Needs review | Topical oil cosmetic activity; not dietary exposure. Needs exclusion unless separately justified. |
| 41540520 | Needs review | Topical wound ointment study; not dietary exposure. Needs exclusion unless separately justified. |
| 41701207 | Needs review | Magnesium/apigenin mouse sleep model; relevant to a broader nutrient-supplement topic, not automatically caffeine evidence. |
| 14147991 | Needs review | Old cooking citation without abstract; insufficient metadata. |
| 40174812 | Needs review | Protein/eGFR citation without abstract; inspect source before deciding. |
| 41138747 | Needs review | Corrigendum to an eggs/fat trial: retain and link correction, not a separate effect study. |

## Parser issue and remediation
Reading raw-versus-normalized abstracts exposed loss of inequality-containing text in the original regex markup stripper. Parser v2 uses HTMLParser and a regression case for `p < 0.05`, confidence intervals and `>` operators. Reparse all normalized documents from preserved raw metadata/JATS before freezing evaluation. Keep pilot-v1 reports as historical measurements, with this caveat.

## Required next validation
Expand screening vocabulary only after reviewing the rules against a frozen mixed sample. Separate title/abstract background relevance from studied nutrition exposure. Independent reviewers should annotate accepted, rejected and unresolved strata. No automated rule change should convert these diagnostic judgments into claimed human validation.

## Completed repair, 7 October
All 973 normalized records were reparsed from preserved raw sources before the delivery freeze. Parser v2 and screening v3 are active; earlier screening decisions remain in history. This remediation does not convert AI diagnostics into independently validated screening.
