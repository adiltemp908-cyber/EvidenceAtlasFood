"""Recompute PDF-aligned metrics from saved rankings and explicit relevance judgments."""
import json
import math
import statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
NAMES={'tfidf':'TF-IDF cosine','bm25':'Flat BM25','structure':'Section-aware BM25','dense':'Semantic search','hybrid':'Hybrid','hybrid_rerank':'Hybrid + reranker'}

def load(name): return json.loads((HERE/name).read_text(encoding='utf-8'))
def save(name,value): (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def calculate(grades,pool_grades,k=10):
    assert len(grades)==k and all(g in (0,1,2,3) for g in grades+pool_grades)
    total_relevant=sum(g>=2 for g in pool_grades)
    assert total_relevant>0
    hits=0;prefix=[];ap_sum=0
    for rank,g in enumerate(grades,1):
        hits+=g>=2
        p=hits/rank;r=hits/total_relevant
        if g>=2: ap_sum+=p
        prefix.append(dict(rank=rank,grade=g,relevant=g>=2,tp=hits,fp=rank-hits,fn=total_relevant-hits,precision=p,recall_pool=r,f1_pool=2*p*r/(p+r) if p+r else 0))
    dcg=sum(g/math.log2(i+2) for i,g in enumerate(grades))
    idcg=sum(g/math.log2(i+2) for i,g in enumerate(sorted(pool_grades,reverse=True)[:k]))
    interp=[max((row['precision'] for row in prefix if row['recall_pool']+1e-12>=level/10),default=0) for level in range(11)]
    return dict(p3=prefix[2]['precision'],p5=prefix[4]['precision'],p10=prefix[-1]['precision'],
        recall10_pool=prefix[-1]['recall_pool'],f1_10_pool=prefix[-1]['f1_pool'],
        ap10_pool=ap_sum/total_relevant,dcg10=dcg,idcg10=idcg,ndcg10=dcg/idcg,
        interpolated_11pt_mean=sum(interp)/11,interpolated_precision=interp,prefix=prefix,
        tp=hits,fp=k-hits,fn_pool=total_relevant-hits,relevant_pool_size=total_relevant)

def validate_formula_examples():
    # PDF pages 44 and 48-50 use linear relevance gains, not 2**grade-1.
    d=lambda a:sum(g/math.log2(i+2) for i,g in enumerate(a))
    assert abs(d([3,2,3,0,1,2])-6.861)<0.002
    assert abs(d([3,2,1,0,1])-5.1488)<0.001
    assert abs(d([3,2,1,0,1])/d([3,2,1,1,0])-0.9916)<0.001
    assert abs(d([2,3,0])/d([3,2,0])-0.9135)<0.001
    # Perfect top-10 can have only half the pool recall and AP when R=20.
    perfect=calculate([3]*10,[3]*20)
    assert perfect['p10']==1 and perfect['recall10_pool']==0.5 and perfect['ap10_pool']==0.5 and perfect['ndcg10']==1
    empty=calculate([0]*10,[3]*5+[0]*10)
    assert empty['ap10_pool']==empty['f1_10_pool']==empty['ndcg10']==0
    assert perfect['interpolated_precision'][6:]==[0]*5
    # Independent AP expression catches denominator and rank errors.
    sample=calculate([3,0,3,1,2,0,0,0,0,0],[3,3,2,2,1,0,0,0,0,0])
    assert abs(sample['ap10_pool']-(1+2/3+3/5)/4)<1e-12

def main():
    validate_formula_examples()
    protocol=load('protocol.json');runs=load('runs.json');pool=load('pool.json');labels=load('judgments.json')
    qrels={(x['query_id'],x['paper_id']):x for x in labels}
    assert len(qrels)==len(labels)==len(pool)
    assert set(qrels)=={(p['query_id'],p['id']) for p in pool}
    assert all(x['reviewer_kind']=='AI' and x['grade'] in (0,1,2,3) and x['rationale'] for x in labels)
    for p in pool:
        label=qrels[p['query_id'],p['id']]
        sources={s['id']:s['text'] for s in p['source_passages']}
        if p['abstract']:sources['abstract']=p['abstract']
        assert all(sources[e['source']]==e['text'] for e in label['evidence'])
    assert {(r['query_id'],r['method']) for r in runs}=={(q['id'],m) for q in protocol['questions'] for m in protocol['methods']}
    assert len(runs)==60
    rows=[]
    for run in runs:
        assert len(run['results'])==len({p['id'] for p in run['results']})==10
        assert [p['rank'] for p in run['results']]==list(range(1,11))
        grades=[qrels[run['query_id'],p['id']]['grade'] for p in run['results']]
        pool_grades=[l['grade'] for l in labels if l['query_id']==run['query_id']]
        metrics=calculate(grades,pool_grades)
        rows.append(dict(query_id=run['query_id'],method=run['method'],grades=grades,latency_ms=run['trace']['latency_ms'],**metrics))
    aggregate={}
    keys=['p3','p5','p10','recall10_pool','f1_10_pool','ap10_pool','dcg10','ndcg10','interpolated_11pt_mean','latency_ms']
    for method in protocol['methods']:
        selected=[r for r in rows if r['method']==method]
        aggregate[method]={k:statistics.mean(r[k] for r in selected) for k in keys}
        aggregate[method]['median_latency_ms']=statistics.median(r['latency_ms'] for r in selected)
        aggregate[method]['interpolated_precision']=[statistics.mean(r['interpolated_precision'][i] for r in selected) for i in range(11)]
        aggregate[method]['strict_grade3_p10']=statistics.mean(sum(g==3 for g in r['grades'])/10 for r in selected)
    result=dict(judgment_kind='AI',queries=10,runs=60,ranked_positions=600,judged_pairs=len(labels),judged_fraction=1.0,
        aggregate=aggregate,per_query=rows,limitations=['Convenience diagnostic questions; some overlap historical development topics.','The evaluation used one set of grades per question–paper pair. Agreement between reviewers was not measured.','Recall, F1, AP and interpolation are judged-pool measures truncated at 10, not full-corpus measures.','No evaluation of generated answers, scientific truth or clinical accuracy.','Single measured search per query/method after warmup; not a load benchmark.'])
    save('metrics.json',result)
    save('validation.json',dict(formula_examples_passed=True,pool_complete=True,rankings_complete=True,judged_fraction=1.0,source_excerpt_checks='Every evidence item exactly matches its corresponding abstract or passage in pool.json.'))
    write_report(protocol,runs,pool,qrels,result)
    write_reviewed_papers(protocol,runs,pool,qrels)
    make_plot(result)
    print(json.dumps(aggregate,indent=2))

def write_report(protocol,runs,pool,qrels,result):
    pct=lambda v:f'{100*v:.1f}%'
    lines=['# EvidenceAtlas Food: 10-query evaluation','', 'Date: 15 November 2026. Evaluation methods adapted from the supplied **08eval (1).pdf**, Lecture 8: Evaluation & Result Summaries.','',
      '**All 310 pooled question–paper pairs were reviewed for relevance.**','',
      '## Setup','',f"- Corpus: {protocol['counts']['searchable_papers']:,} searchable papers; {protocol['counts']['passages']:,} source passages.",
      f"- Corpus fingerprint: `{protocol['corpus']}`.",f"- Source commit: `{protocol['git_commit']}`; implementation hashes are recorded in protocol.json.",
      f"- Six existing retrieval methods x 10 questions x 10 results = 600 ranked positions; {len(pool)} distinct query-paper pairs, all reviewed.",
      '- Questions and information needs were fixed before viewing these rankings. Five easy and five medium questions; difficulty is a qualitative label, not measured.',
      '- Query expansion enabled for every method, no metadata filters, recency preference disabled. No ranking changes, ingestion, model tuning or post-result query rewrites.',
      '- Relevance grades: 0 = irrelevant, 1 = related/background, 2 = directly useful but partial/applicability-limited, 3 = directly applicable. Binary relevance is grade >= 2.',
      '- Review screened titles and query-focused abstract excerpts, then inspected complete abstracts and retrieved passages for ambiguous cases. This was not an exhaustive full-paper review. Full stored abstracts and retrieved passages are retained for audit.',
      '- Reviews and null findings can be relevant. Background citations in primary studies are not treated as that study\'s own results; review articles can synthesize cited evidence. Human-health questions require human-applicable evidence; laboratory cooking experiments qualify for the cooking question.',
      '- Papers were reviewed in paper-ID order with method names and ranks hidden.',
      '- Rankings were collected in one read-only SQLite transaction; the corpus fingerprint and active index pointer were checked unchanged. Saved source text and rankings are retained for audit.',
      '', '## The 10 questions','', '| ID | Difficulty | Question |','|---|---|---|']
    lines += [f"| {q['id']} | {q['difficulty']} | {q['query']} |" for q in protocol['questions']]
    lines += ['', '## Measures and PDF mapping','',
      '| Measure | Definition used | PDF pages |','|---|---|---|',
      '| Precision@k | Relevant papers among first k / k; k = 3, 5, 10 | 9-10, 21, 39 |',
      '| Pool Recall@10 | Relevant top-10 papers / all relevant papers in the six-method judged pool | 9-10, 40 |',
      '| Pool F1@10 | 2PR/(P+R), zero when both are zero | 12-18 |',
      '| Pool AP@10 and MAP@10 | AP = sum of P@r at relevant ranks r <= 10 / total relevant pool papers; MAP = mean across 10 queries | 37-38 |',
      '| 11-point interpolation | Maximum observed precision at pool recall >= each of 0.0, 0.1, ..., 1.0; zero beyond retrieved depth | 21-36 |',
      '| DCG@10 | Sum grade_r / log2(r+1), using the lecture\'s linear gains | 41-45 |',
      '| nDCG@10 | DCG divided by ideal DCG from the common judged pool, at the same cutoff | 46-50 |',
      '| Latency | One measured search per query/method after model warmup | 3 |','',
      '**Denominator limitation:** Only the union of the six top-10 lists is judged, not the whole corpus. R is the number of grade >= 2 papers in that pool. We therefore label recall/F1/AP as pool-relative and MAP as MAP@10. Unjudged corpus papers are not assumed irrelevant. Scores depend on pool composition and depth.','',
      '**nDCG convention:** The lecture uses linear relevance gains; the project\'s older helper uses exponential gains, so a separate calculator follows this PDF. For fair comparisons, every method shares one query-specific ideal ranking from the pooled judgments. The lecture\'s final illustrative example sorts each individual returned list; that can conceal missed highly relevant papers, so those list-specific denominators are not used here.','',
      'Classification accuracy is omitted for the reason given on PDF pages 14-16. Indexing speed, monetary cost, user satisfaction and full-corpus recall were not measured. No summary-generation or nutrition-answer accuracy evaluation is implied.','',
      '## Method comparison','', 'Each value is the arithmetic mean across the same 10 queries. Mean F1 is the mean of per-query F1, not F1 computed from mean P and R.','',
      '| Method | P@3 | P@5 | P@10 | Pool R@10 | Pool F1@10 | Pool MAP@10 | nDCG@10 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for m,a in result['aggregate'].items():
        lines.append('| '+NAMES[m]+' | '+' | '.join(pct(a[k]) for k in ['p3','p5','p10','recall10_pool','f1_10_pool','ap10_pool','ndcg10'])+' |')
    lines += ['', '**Interpretation:** Hybrid + reranker has the highest observed P@10 and nDCG@10 on this set, while semantic search has the highest P@3 and P@5. The P@10 difference between those two methods is only one relevant ranked position out of 100; no statistically reliable superiority is claimed.', '',
        '**Grading sensitivity:** The primary binary metrics count grades 2 and 3 as relevant, including directly useful partial matches. If only grade 3 (fully applicable evidence) is counted, P@10 is '+', '.join(f"{NAMES[m]} {pct(a['strict_grade3_p10'])}" for m,a in result['aggregate'].items())+'. The graded nDCG scores already distinguish partial from fully applicable evidence.']
    lines += ['', '| Method | Mean DCG@10 | 11-point mean precision | Mean search time | Median search time |','|---|---:|---:|---:|---:|']
    for m,a in result['aggregate'].items():
        lines.append(f"| {NAMES[m]} | {a['dcg10']:.3f} | {pct(a['interpolated_11pt_mean'])} | {a['latency_ms']/1000:.3f} s | {a['median_latency_ms']/1000:.3f} s |")
    lines += ['', 'Warmup/loading excluded from measured search times. Method execution order was rotated by query. Single-machine, sequential measurements are descriptive, not a throughput or statistically controlled performance benchmark.','',
      '## Default retrieval pipeline, by question','', '| Query | Relevant pool | Relevant / 10 | P@3 | P@5 | P@10 | Pool R@10 | Pool F1@10 | Pool AP@10 | nDCG@10 |','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in result['per_query']:
        if r['method']=='hybrid_rerank':
            lines.append(f"| {r['query_id']} | {r['relevant_pool_size']} | {r['tp']} | "+' | '.join(pct(r[k]) for k in ['p3','p5','p10','recall10_pool','f1_10_pool','ap10_pool','ndcg10'])+' |')
    lines += ['', 'The default pipeline is Hybrid + reranker; these benchmark runs disable the optional recency preference.','',
      '## Averaged precision-recall curves','', '![11-point interpolated precision versus judged-pool recall](precision-recall.png)','',
      '| Method | '+ ' | '.join(f'{i/10:.1f}' for i in range(11))+' |', '|---|'+'---:|'*11]
    for m,a in result['aggregate'].items():lines.append('| '+NAMES[m]+' | '+' | '.join(pct(v) for v in a['interpolated_precision'])+' |')
    lines += ['', 'Zeros at high recall levels mean the top-10 run did not reach those pool-recall levels. They do not characterize results beyond rank 10.','', '## Complete per-query metrics','', '| Query | Method | Grades in rank order | P@10 | Pool R@10 | Pool AP@10 | nDCG@10 |','|---|---|---|---:|---:|---:|---:|']
    for r in sorted(result['per_query'],key=lambda r:(r['query_id'],protocol['methods'].index(r['method']))):
        lines.append(f"| {r['query_id']} | {NAMES[r['method']]} | {','.join(map(str,r['grades']))} | "+' | '.join(pct(r[k]) for k in ['p10','recall10_pool','ap10_pool','ndcg10'])+' |')
    lines += ['', '## Reproduction and audit files','',
      '- `protocol.json`: queries, information needs, grading rules, corpus/model/code identities and configuration.',
      '- `runs.json`: actual ranked papers, scores, passages and execution traces.',
      '- `pool.json`: merged query-paper review pool with source text.',
      '- `judgments.json`: every grade, rationale, review metadata and exact stored evidence text.',
      '- `REVIEWED_PAPERS.md`: readable paper-by-paper grades/rationales and top-10 lists for Hybrid + reranker.',
      '- `metrics.json`: all metrics, contingency counts and rank-by-rank precision/recall/F1.',
      '- `validation.json`: formula-example and completeness checks.',
      '- `evaluate.py`: recompute metrics, this report and the curve from saved data.',
      '', 'Run `python evaluation/pdf-easy-medium-10-2026-11-15/evaluate.py` from the app folder. Recomputing scores needs no search-model inference. `collect.py` preserves existing rankings by refusing to overwrite them.','',
      '## Limits of interpretation','']
    lines += ['- '+x for x in result['limitations']]
    lines += ['- Ten questions do not support a claim that one method is universally superior. Statistical significance and confidence intervals are not claimed.',
      '- An abstract can support relevance without establishing study quality, certainty, causal validity or the correctness of a generated answer.',
      '- The saved rankings and grades permit rescoring under different relevance thresholds.']
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def write_reviewed_papers(protocol,runs,pool,qrels):
    lines=['# Reviewed papers and actual ranked results','','The pooled papers were reviewed for relevance. Grades 2 and 3 count toward the primary precision/recall measures. See RESULTS.md for the protocol and limitations.']
    for q in protocol['questions']:
        qid=q['id'];lines += ['',f"## {qid}: {q['query']}",'',q['information_need'],'','### Hybrid + reranker: actual top 10','','| Rank | Paper | Grade | Reason |','|---:|---|---:|---|']
        run=next(r for r in runs if r['query_id']==qid and r['method']=='hybrid_rerank')
        for p in run['results']:
            label=qrels[qid,p['id']];title=p['title'].replace('|','/').replace('<i>','').replace('</i>','')
            link=f"https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/" if p.get('pmid') else f"https://europepmc.org/article/MED/{p['id'].split(':')[-1]}"
            lines.append(f"| {p['rank']} | [{title}]({link}) | {label['grade']} | {label['rationale']} |")
        lines += ['','### All pooled papers','','| Paper ID | Title | Grade | Reason |','|---|---|---:|---|']
        for p in pool:
            if p['query_id']==qid:
                label=qrels[qid,p['id']];title=p['title'].replace('|','/').replace('<i>','').replace('</i>','')
                lines.append(f"| {p['id']} | {title} | {label['grade']} | {label['rationale']} |")
    (HERE/'REVIEWED_PAPERS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

def make_plot(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(10.5,6.5),layout='constrained')
    for m,a in result['aggregate'].items():
        ax.plot([i/10 for i in range(11)],a['interpolated_precision'],marker='o',markersize=4,label=NAMES[m])
    ax.set(xlabel='Recall relative to judged pool',ylabel='Interpolated precision (mean over 10 queries)',xlim=(0,1),ylim=(0,1.03),title='EvidenceAtlas Food: 11-point precision-recall comparison')
    ax.set_xticks([i/10 for i in range(11)]);ax.grid(alpha=.22);ax.legend(loc='upper right',fontsize=9)
    fig.supxlabel('Reviewed pooled judgments | Top-10 rankings only | 15 November 2026',fontsize=10)
    fig.savefig(HERE/'precision-recall.png',dpi=180);plt.close(fig)

if __name__=='__main__':main()
