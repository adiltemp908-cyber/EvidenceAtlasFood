import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent
notes={};qid=None
for l in (P/'review_notes.txt').read_text().splitlines():
 if re.fullmatch(r'Q\d\d',l):qid=l;notes[qid]=[]
 elif l:notes[qid].append(int(l.split('|')[1]))
terms={
'Q01':(r'coffee|caffeine',r'sleep|insomnia'),
'Q02':(r'salt|sodium',r'blood pressure|\bBP\b'),
'Q03':(r'fiber|fibre|psyllium',r'constipat|stool|bowel'),
'Q04':(r'milk|dairy',r'bone|fracture'),
'Q05':(r'boil',r'vitamin\s*C|ascorbic'),
'Q06':(r'oat',r'LDL|cholesterol'),
'Q07':(r'nuts?\b|almond|walnut|peanut',r'weight|BMI|adipos|obes'),
'Q08':(r'yogurt|yoghurt',r'lactose|intoleran|digest'),
'Q09':(r'sugar|\bSSB|soft drink',r'diabet'),
'Q10':(r'protein',r'hypertrophy|muscle mass'),
}
pool=json.loads((P/'pool.json').read_text(encoding='utf-8'))
for q in sys.argv[1:]:
 for n,p in enumerate([x for x in pool if x['query_id']==q],1):
  if notes[q][n-1]>1:continue
  candidates=[]
  for s in p['source_passages']:
   if s['zone'] in ('title','abstract'):continue
   for sentence in re.split(r'(?<=[.!?])\s+(?=[A-Z])',s['text']):
    if all(re.search(t,sentence,re.I) for t in terms[q]): candidates.append(s['id']+' '+sentence)
  if candidates:
   print(f'\n{q} [{n}] {p["title"]}')
   for s in candidates[:2]:print(s[:1700])
