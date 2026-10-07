from dataclasses import dataclass,field
from typing import Literal

Stance=Literal['supports','contradicts','insufficient to establish']
Compatibility=Literal['matches','differs','unknown']
Availability=Literal['full-text','abstract-only','metadata-only']

@dataclass(frozen=True)
class SourceSpan:
    paper_id: str
    passage_id: str
    start: int
    end: int
    quote: str
    def validate(self,store):
        row=store.db.execute('SELECT paper_id,text FROM passages WHERE id=?',(self.passage_id,)).fetchone()
        if not row or row['paper_id']!=self.paper_id or self.start<0 or self.end<=self.start or row['text'][self.start:self.end]!=self.quote:
            raise ValueError('Source span does not match the frozen passage')

@dataclass(frozen=True)
class EvidenceJudgment:
    claim_id: str
    paper_id: str
    reviewer_id: str
    reviewer_kind: Literal['human','AI']
    qualifications: str
    relevance: int
    stance: Stance
    compatibility: Compatibility
    corpus: str
    rationale: list[SourceSpan]=field(default_factory=list)
    def validate(self,store):
        if self.relevance not in (0,1,2,3):raise ValueError('Relevance grade must be 0–3')
        if self.stance not in ('supports','contradicts','insufficient to establish'):raise ValueError('Invalid stance')
        if self.compatibility not in ('matches','differs','unknown'):raise ValueError('Invalid compatibility')
        if self.reviewer_kind not in ('human','AI') or not self.reviewer_id.strip():raise ValueError('Reviewer provenance required')
        if self.corpus!=store.fingerprint():raise ValueError('Judgment corpus differs from evaluation snapshot')
        if self.relevance>=2 and not self.rationale:raise ValueError('Direct evidence needs exact rationale spans')
        for span in self.rationale:
            if span.paper_id!=self.paper_id:raise ValueError('Rationale must belong to judged paper')
            span.validate(store)
