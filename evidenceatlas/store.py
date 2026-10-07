from __future__ import annotations
import hashlib
import json
import sqlite3

SCHEMA="""
CREATE TABLE IF NOT EXISTS papers(id TEXT PRIMARY KEY, pmid TEXT UNIQUE, pmcid TEXT UNIQUE, doi TEXT, title TEXT NOT NULL, abstract TEXT, year INTEGER, species TEXT, availability TEXT, metadata TEXT NOT NULL, updated TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS papers_doi ON papers(doi);
CREATE TABLE IF NOT EXISTS discoveries(paper_id TEXT, topic TEXT, query_hash TEXT, decision TEXT, reason TEXT, PRIMARY KEY(paper_id,topic,query_hash));
CREATE TABLE IF NOT EXISTS passages(id TEXT PRIMARY KEY,paper_id TEXT NOT NULL,section TEXT,zone TEXT,text TEXT,ordinal INTEGER,payload TEXT NOT NULL, FOREIGN KEY(paper_id) REFERENCES papers(id));
CREATE INDEX IF NOT EXISTS passage_parent ON passages(paper_id);
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS failures(id TEXT PRIMARY KEY,paper_id TEXT,stage TEXT,message TEXT,updated TEXT);
CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY,created TEXT,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS screening_history(paper_id TEXT,topic TEXT,query_hash TEXT,decision TEXT,reason TEXT,version TEXT,changed TEXT);
"""

class Store:
    def __init__(self,path=':memory:'):
        self.db=sqlite3.connect(str(path))
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA cache_size=-16384')
        self.db.executescript(SCHEMA)

    def canonical(self,record):
        for field in ('pmid','pmcid','doi'):
            value=record.get(field)
            if value:
                if field=='doi':value=value.lower().strip()
                row=self.db.execute(f'SELECT id FROM papers WHERE {field}=?',(value,)).fetchone()
                if row:return row[0]
        return 'MED:'+str(record.get('pmid') or record['id'])

    def save(self,paper,passages,topic,qhash,decision,reason):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO papers VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                tuple(paper.get(k) for k in ('id','pmid','pmcid','doi','title','abstract','year','species','availability'))+(json.dumps(paper['metadata']),paper['updated']))
            self.db.execute('INSERT OR REPLACE INTO discoveries VALUES(?,?,?,?,?)',(paper['id'],topic,qhash,decision,reason))
            self.db.execute('DELETE FROM passages WHERE paper_id=?',(paper['id'],))
            self.db.executemany('INSERT INTO passages VALUES(?,?,?,?,?,?,?)',[(p['id'],paper['id'],p['section'],p['zone'],p['text'],p['ordinal'],json.dumps(p)) for p in passages])

    def fingerprint(self):
        h=hashlib.sha256()
        for r in self.db.execute('SELECT id,payload FROM passages ORDER BY id'):
            h.update((r[0]+r[1]).encode())
        return h.hexdigest()

    def counts(self):
        return {"papers":self.db.execute('SELECT count(*) FROM papers').fetchone()[0],
                "searchable_papers":self.db.execute('SELECT count(DISTINCT paper_id) FROM passages').fetchone()[0],
                "passages":self.db.execute('SELECT count(*) FROM passages').fetchone()[0],
                "availability":dict(self.db.execute('SELECT availability,count(*) FROM papers GROUP BY availability')),
                "screening":dict(self.db.execute('SELECT decision,count(*) FROM discoveries GROUP BY decision')),
                "topics":[dict(r) for r in self.db.execute('SELECT topic,decision,count(DISTINCT paper_id) AS papers FROM discoveries GROUP BY topic,decision')],
                "failures":self.db.execute('SELECT count(*) FROM failures').fetchone()[0]}

    def paper(self,pid):
        row=self.db.execute('SELECT * FROM papers WHERE id=?',(pid,)).fetchone()
        if not row:return None
        p=dict(row);p['metadata']=json.loads(p['metadata'])
        p['passages']=[json.loads(r[0]) for r in self.db.execute('SELECT payload FROM passages WHERE paper_id=? ORDER BY ordinal',(pid,))]
        return p
