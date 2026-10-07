export type Availability = 'full-text' | 'abstract-only' | 'metadata-only';
export type Stance = 'supports' | 'contradicts' | 'insufficient to establish';
export type Compatibility = 'matches' | 'differs' | 'unknown';
export interface SourceSpan {paper_id:string;passage_id:string;start:number;end:number;quote:string}
export interface Passage {id:string;paper_id:string;section:string;zone:string;text:string;start:number;end:number;paragraph:string;gaps:string[]}
export interface PaperHit {id:string;title:string;pmid:string|null;pmcid:string|null;availability:Availability;species:string;year:number|null;score:number;rank:number;passages:Passage[];score_components:Record<string,unknown>[]}
export interface CandidateField {value:string;passage_id:string;start:number;end:number;source_text:string;status:string}
export interface StudyContext {paper_id:string;fields:Record<string,CandidateField[]>}
export interface SearchRun {query:string;results:PaperHit[];trace:{method:string;index:{corpus:string};latency_ms:number;filters?:Record<string,unknown>};evidence:{summary:string;coverage:string;scientific_certainty:string;studies:StudyContext[]};intent?:{scope:string;ambiguities:string[]};experimental_analysis?:unknown}
export interface Judgment {claim_id:string;paper_id:string;reviewer_id:string;reviewer_kind:'human'|'AI';relevance:0|1|2|3;stance:Stance;compatibility:Compatibility;corpus:string;rationale:SourceSpan[]}
