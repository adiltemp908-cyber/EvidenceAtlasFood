"""Build the designed course report. Requires ReportLab; run evaluate_report.py first."""
import json, os
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'evaluation/report-v2/metrics.json').read_text())
W,H=595.276,841.89
GREEN,INK,MUTED='#123524','#173b2a','#5e6d61'
PAPER,WHITE,PALE,LINE,ACCENT='#f5f5ef','#fffef9','#e7efdf','#dde3d8','#bad49d'
FONTS={}
for name,file,fallback in [('body','segoeui.ttf','Helvetica'),('bold','segoeuib.ttf','Helvetica-Bold'),('serif','georgia.ttf','Times-Roman'),('italic','georgiai.ttf','Times-Italic')]:
    path=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/file
    if path.exists():
        pdfmetrics.registerFont(TTFont('EA-'+name,str(path)));FONTS[name]='EA-'+name
    else:FONTS[name]=fallback
OUT=ROOT/'docs/EvidenceAtlas_Food_Report.pdf'
c=canvas.Canvas(str(OUT),pagesize=(W,H))
c.setTitle('EvidenceAtlas Food | From food questions to scientific evidence')
c.setAuthor('EvidenceAtlas Food - AI-assisted course project')
md=[];page_no=0
def box(x,t,w,h,fill=WHITE,r=10,stroke=None):
    c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke or fill));c.roundRect(x,H-t-h,w,h,r,fill=1,stroke=bool(stroke))
def text(s,x,t,size=10,font='body',color=INK):
    c.setFillColor(HexColor(color));c.setFont(FONTS.get(font,font),size);c.drawString(x,H-t-size,s)
def para(s,x,t,w=491,size=10,leading=15,font='body',color=INK,record=True):
    style=ParagraphStyle('p',fontName=FONTS[font],fontSize=size,leading=leading,textColor=HexColor(color))
    p=Paragraph(escape(s),style);_,height=p.wrap(w,700)
    if t+height>785:raise ValueError(f'Page {page_no}: overflow: {s[:60]}')
    p.drawOn(c,x,H-t-height)
    if record:md.append(s+'\n')
    return t+height
def eyebrow(s,x=52,t=84,color=MUTED):text(s.upper(),x,t,8,'bold',color)
def line(x,t,w=491,color=LINE):
    c.setStrokeColor(HexColor(color));c.setLineWidth(.7);c.line(x,H-t,x+w,H-t)
def leaf(x,t,scale=1):
    c.saveState();c.translate(x,H-t);c.scale(scale,scale);c.setStrokeColor(HexColor(ACCENT));c.setLineWidth(1.3)
    p=c.beginPath();p.moveTo(0,-64);p.curveTo(-10,-10,14,36,56,54);p.curveTo(60,4,44,-48,0,-64);c.drawPath(p)
    c.line(0,-64,45,34);c.line(12,-30,43,-17);c.line(20,-12,7,7);c.line(30,10,50,19);c.restoreState()
def page(section,title,subtitle):
    global page_no
    if page_no:c.showPage()
    page_no+=1;c.setFillColor(HexColor(PAPER));c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(HexColor(GREEN));c.rect(0,0,12,H,fill=1,stroke=0)
    text('EvidenceAtlas',52,28,13,'serif');text('FOOD',146,33,7,'bold',MUTED)
    text('CSD358  /  TRACK T6',424,33,7.5,'body',MUTED);line(52,58)
    text('FOOD QUESTIONS. SCIENTIFIC SOURCES.',52,807,6.7,'body',MUTED);text(f'{page_no:02d} / 07',500,805,8,'bold',MUTED)
    eyebrow(section);para(title,52,108,491,29,35,'serif');para(subtitle,52,158,491,10.5,16,color=MUTED)
    md.extend(['## '+title,''])
def card(x,t,w,h,n,title,body):
    box(x,t,w,h);text(n,x+17,t+14,8,'bold',MUTED);para(title,x+17,t+37,w-34,17,22,'serif');para(body,x+17,t+70,w-34,9.5,14)
def pct(v):return f'{v*100:.1f}%'
def scores(key):return [pct(DATA['metrics'][key]['precision'][str(k)]) for k in (3,5,10)]
def table(headers,rows,x,t,widths,rh=44):
    width=sum(widths);box(x,t,width,30,GREEN,6);dx=x
    for h,w in zip(headers,widths):para(h,dx+12,t+8,w-24,8,11,'bold',WHITE,False);dx+=w
    t+=30
    for i,row in enumerate(rows):
        box(x,t,width,rh,WHITE if i%2==0 else PALE,0);dx=x
        for j,(cell,w) in enumerate(zip(row,widths)):
            para(str(cell),dx+12,t+10,w-24,9,12,'body' if j==0 else 'bold',INK,False);dx+=w
        t+=rh
    md.extend(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |'])
    md.extend('| '+' | '.join(map(str,row))+' |' for row in rows);md.append('')

page('THE PROJECT','EvidenceAtlas Food','')
box(30,75,W-60,355,GREEN,16);eyebrow('Information retrieval for everyday food questions',54,101,ACCENT)
text('EvidenceAtlas',54,132,41,'serif',WHITE);text('Food',54,181,41,'italic',ACCENT)
para('From a food question to the studies behind it.',54,254,390,22,29,'serif',WHITE)
para('A working search and comparison tool for everyday readers, dietitians and researchers.',54,335,366,11,17,color='#d6e1cd');leaf(444,207,.9)
eyebrow('What we built, in five steps',52,457)
steps=[('01','Collect real literature','Find nutrition papers in PubMed and Europe PMC.'),('02','Keep the paper structure','Separate abstracts, methods, results and other sections.'),('03','Build and combine searches','Match exact terms and meaning, then rank candidate papers.'),('04','Make the evidence inspectable','Open source passages, compare studies and save an investigation.'),('05','Measure what the search returns','Review ranked papers and calculate Precision@3, @5 and @10.')]
for i,(n,title,body) in enumerate(steps):
    y=484+i*48;box(52,y,29,29,PALE,7);text(n,59,y+7,9,'bold');text(title,94,y-1,10.5,'bold');para(body,94,y+16,441,9,12,color=MUTED)
line(52,741);text('950 searchable papers',52,755,11,'serif');text('494 full texts',242,755,11,'serif');text('37,975 passages',407,755,11,'serif')

page('01 / COLLECT AND ORGANIZE','Start with the literature.','The collection was built from scientific records, then turned into searchable sections.')
for x,big,label in [(52,'973','unique records'),(220,'494','ingested full texts'),(388,'12','nutrition topic groups')]:
    box(x,210,155,84);text(big,x+17,219,31,'serif');text(label,x+17,264,8.5,'body',MUTED)
para('We searched by scientific subject headings and by words in titles and abstracts. The topic plan covered foods, nutrients, meal timing and preparation: for example caffeine and sleep, sodium and blood pressure, and cooking and vitamin retention.',52,317,491,10.3,16)
eyebrow('The path from a record to evidence',52,402)
for i,(a,b) in enumerate([('DISCOVER','MeSH + title/abstract'),('SCREEN','Nutrition relevance'),('DEDUPLICATE','PMID / PMCID / DOI'),('PARSE','Sections + passages')]):
    x=52+i*125;box(x,426,116,62,PALE,8);text(a,x+10,438,7.2,'bold');para(b,x+10,456,97,8.4,11,record=False)
    if i<3:text('>',x+117,447,9,'bold',MUTED)
para('When an open-access full text was available, the JATS XML was downloaded and parsed. Each passage keeps its parent paper, section name and position. This lets a result open at the relevant evidence while the reader checks the surrounding methods or discussion.',52,512,491,10.3,16)
card(52,601,238,134,'FULL TEXT','More than the abstract','494 records contain ingested full text. Methods, results, discussion and tables can be inspected where the source supplies them.')
card(305,601,238,134,'ABSTRACT ONLY','A visible limit','473 records have abstracts only; six contain metadata only. These availability labels stay visible rather than implying a complete paper was read.')
para('Raw responses and content hashes are retained. The first 77-record pilot included 42 full texts and informed later collection growth.',52,752,491,8.5,12,color=MUTED)

page('02 / BUILD THE SEARCH','Find the words. Find the meaning.','Different retrieval methods solve different parts of the same search problem.')
card(52,211,238,150,'LEXICAL SEARCH','Exact terms and structure','TF-IDF and BM25 use an explicit index of words, counts and positions. Section-aware BM25 can give a match in results more weight than a match in background text.')
card(305,211,238,150,'SEMANTIC SEARCH','Related wording','MiniLM turns each passage into a 384-number vector. A question is encoded the same way, so related wording can match even when the exact words differ.')
para('All 37,975 passage vectors are complete. The model reads up to 256 tokens per passage; 2,723 longer passages were truncated for encoding. Their complete text is still stored and searchable through the lexical index.',52,385,491,10,15)
box(52,463,491,136,GREEN);eyebrow('Hybrid + relevance ranking',70,479,ACCENT)
para('Bring candidates together, then look again.',70,504,448,20,25,'serif',WHITE)
para('Reciprocal Rank Fusion combines lexical and semantic rankings. A MiniLM cross-encoder then reorders up to 20 candidates using the question, paper title and a selected passage.',70,548,449,9.8,15,color='#d6e1cd')
eyebrow('What can be inspected',52,625)
para('The search trace exposes the terms, expansions, scores, section weights, filters and corpus version. Quoted phrases use token positions; the lexical methods also support AND, OR and NOT. Year, full-text and other filters help narrow the search.',52,649,491,10,15)
para('The reranker sees a selected passage, not the entire paper. Its score estimates relevance to the question; it does not determine whether a scientific claim is true.',52,724,491,9.5,14,color=MUTED)

page('03 / USE THE PRODUCT','A search result you can open.','The interface carries the question through to source inspection and study comparison.')
image=ImageReader(str(ROOT/'docs/screenshots/report-home.png'));iw,ih=image.getSize();image_h=491*ih/iw
box(49,208,497,image_h+6,WHITE,8,LINE);c.drawImage(image,52,H-211-image_h,width=491,height=image_h,mask='auto')
text('ACTUAL LOCAL INTERFACE  /  PHTHALO GREEN #123524',52,222+image_h,7,'bold',MUTED)
y=246+image_h
for x,title,body in [(52,'Everyday','A concise way to search and open relevant evidence.'),(220,'Dietitian','More study context and side-by-side paper comparison.'),(388,'Research','Retrieval traces and experimental model diagnostics.')]:
    box(x,y,155,112,WHITE,8);text(title,x+13,y+13,15,'serif');para(body,x+13,y+42,129,9,13)
para('A result card shows the paper and evidence availability. Opening it reveals source passages and surrounding sections. Readers can compare up to four papers, save notes with an investigation, and export evidence for later use.',52,y+135,491,10,15)

page('04 / TEST THE RETRIEVAL','What counts as a useful result?','Precision measures the proportion of retrieved papers that help address the question.')
box(52,211,491,90,GREEN);text('Precision@k = relevant papers in the first k / k',70,230,17,'serif',WHITE)
para('For example: eight relevant papers among the first ten gives Precision@10 = 80%.',70,267,448,9.5,14,color='#d6e1cd')
para('We ran six everyday questions with hybrid plus relevance ranking and inspected the top ten papers for each. Four query rewrites were also tried. Two matched BM25 searches provide a small baseline comparison. The corpus and retrieval settings were kept fixed.',52,325,491,10.2,16)
table(['Grade','How the paper is treated'],[['2 - relevant','Directly useful for part of the question; relevant null findings count too.'],['1 - related','Background, or a mismatch in food, preparation or outcome.'],['0 - off-topic','Does not address the exposure and outcome being searched.']],52,412,[113,378],43)
para('Only grade 2 counts toward precision. Judgments use titles, abstracts and selected source sections. They were made by AI, not an independent human panel; they assess retrieval relevance rather than study validity or certainty.',52,587,491,9.8,15)
eyebrow('A concrete query refinement',52,663)
para('"Does eating salt raise blood pressure?" was rewritten as "Dietary sodium reduction blood pressure clinical trials". Precision@10 rose from 60% to 80%, while Precision@3 fell from 100% to 66.7%. The added detail found more useful papers overall but did not improve every rank.',52,687,491,9.5,14)
para('The milk and egg rewrites were screened but not retained. All attempted queries and their review status are saved.',52,759,491,8.5,12,color=MUTED)

page('05 / READ THE RESULTS','Useful results, at three depths.','Five selected presentation examples using hybrid plus relevance ranking.')
rows=[[DATA['metrics'][key]['query']]+scores(key) for key in DATA['selected']]
table(['Query','P@3','P@5','P@10'],rows,52,211,[260,77,77,77],54)
para('Selected-example mean',52,523,217,11,16,'serif')
for x,k in zip([322,399,476],(3,5,10)):text(pct(DATA['selected_mean'][str(k)]),x,522,11,'bold')
line(52,551)
para(f"These examples were chosen after inspecting results. The original six-question set, including the weaker egg query, averaged {pct(DATA['original_six_mean']['3'])}, {pct(DATA['original_six_mean']['5'])} and {pct(DATA['original_six_mean']['10'])} at ranks 3, 5 and 10. The selected table is a demonstration, not a general accuracy estimate.",52,568,491,9.5,14)
eyebrow('Same queries, different method',52,636)
table(['Two-query paired comparison','P@3','P@5','P@10'],[['Flat BM25']+[pct(DATA['paired_baseline_mean'][str(k)]) for k in (3,5,10)],['Hybrid + relevance ranking']+[pct(DATA['paired_hybrid_mean'][str(k)]) for k in (3,5,10)]],52,658,[260,77,77,77],31)
para('Pair: coffee/sleep and the refined sodium query. Hybrid did better at ranks 5 and 10; BM25 did better at rank 3. Two queries cannot establish a general winner.',52,759,491,8.5,12,color=MUTED)

page('06 / DELIVERY AND NEXT STEPS','A working system, with room to grow.','The project connects acquisition, full-text retrieval and source inspection in one local workflow.')
card(52,211,238,143,'WHAT IS WORKING','Search to comparison','Real literature ingestion, section and positional indexes, passage embeddings, hybrid retrieval, reranking, source navigation and saved investigations.')
card(305,211,238,143,'WHAT WAS CHECKED','Code and interface','23 core/dense tests and the TypeScript check passed in the delivery check. Earlier browser checks exercised search, source viewing, comparison, saving and export.')
para('The Track T6 contribution is the use of document structure throughout the workflow: sections influence retrieval, passages link back to papers, and the reader can inspect how a result was found. The ranking algorithms are established methods. The project work lies in combining them with food-specific acquisition and an interface that keeps study context visible.',52,381,491,10,15)
box(52,477,491,128,PALE);eyebrow('Run and reproduce',70,492)
text('python -m evidenceatlas.cli serve --port 8765',70,517,10,'Courier')
para('Run from the app folder with EAF_ROOT set to the data directory, then open http://127.0.0.1:8765/. README.md includes full installation instructions.',70,540,449,9.4,14)
text('python scripts/evaluate_report.py',70,580,10,'Courier')
para('The evaluation script recalculates every reported score from saved rankings and labels. Papers, indexes, models and caches stay on E:. The measured project uses about 4.1 GB; acquisition reserves 40 GB free and supports further growth. Models run locally on CPU without a paid inference API.',52,629,491,9.8,15)
para('Next: improve coverage where relevant papers are missing, select better passages for reranking, and repeat the evaluation with independent reviewers. A larger model alone will not fill gaps in the corpus.',52,704,491,9.8,15)
para('AI assistance was used for implementation, documentation and relevance judgments. Team ownership and the course demo recording still need to be supplied for submission.',52,759,491,8.2,12,color=MUTED)
c.save();(ROOT/'docs/REPORT.md').write_text('# EvidenceAtlas Food\n\n'+'\n'.join(md),encoding='utf-8');print(OUT)
