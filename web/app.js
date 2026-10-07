function $(s) { return document.querySelector(s); }
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const number = v => Number(v || 0).toLocaleString();
let current = null, audience = 'everyday', selected = new Set(), lastSession = null, history = [];
async function api(path, options) { const r = await fetch(path, options); let data = await r.json(); if (!r.ok)
    throw Error(data.error || `Request failed (${r.status})`); return data; }
function status(message, error = false) { $('#status').textContent = message; $('#status').className = error ? 'error' : ''; }
function highlight(text, query) { const words = [...new Set((query || '').toLowerCase().match(/[a-z0-9]+/g) || [])].filter(w => w.length > 3).slice(0, 20); if (!words.length)
    return esc(text); const re = new RegExp(`(${words.join('|')})`, 'gi'); return text.split(re).map((p, i) => i % 2 ? `<mark>${esc(p)}</mark>` : esc(p)).join(''); }
function snapshot() { return { query: current.query, run: current, history, notes: $('#notes')?.value || '', selected: [...selected], scope: 'Retrieved local collection; not a systematic review', uncertainty: current.evidence.coverage }; }
function download(value, name, type = 'application/json') { const url = URL.createObjectURL(new Blob([typeof value === 'string' ? value : JSON.stringify(value, null, 2)], { type })); const a = document.createElement('a'); a.href = url; a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
function sectionLink(pid, pid2, label) { return `<button class="inspect" data-paper="${esc(pid)}" data-passage="${esc(pid2 || '')}">${esc(label)}</button>`; }
function fieldsHTML(study) { return `<p class="meta">Candidate mentions from source text; attribution to the study and applicability require review.</p><div class="fields">${Object.entries(study.fields).map(([field, values]) => `<div class="field"><b>${esc(field)}</b><div>${values.length ? values.slice(0, 3).map(v => sectionLink(study.paper_id, v.passage_id, v.value)).join(' ') : '<small>Unknown / not extracted</small>'}</div><small>Context compatibility: unknown</small></div>`).join('')}</div>`; }
function render() {
    if (!current)
        return;
    $('#explore').classList.add('has-results');
    const run = current;
    const studies = Object.fromEntries(run.evidence.studies.map(s => [s.paper_id, s]));
    $('#resultsarea').innerHTML = `<div class="resultshead"><div><h2>Evidence to explore <span class="meta">${run.results.length} papers</span></h2><p>${esc(run.query)}</p></div><div class="actions"><button id="comparebtn">Compare selected (${selected.size})</button><button id="savebtn">Save investigation</button><button id="exportbtn">Export evidence</button></div></div><div class="resultsgrid"><div>${run.results.length ? run.results.map(p => `<article class="paper"><div class="tags"><span class="tag ${p.availability === 'full-text' ? '' : 'abstract'}">${p.availability === 'full-text' ? 'FULL TEXT' : 'ABSTRACT ONLY'}</span><span class="tag">${esc(p.species)}</span><span class="tag">${esc(p.year || 'Year unknown')}</span></div><h3>${sectionLink(p.id, null, p.title)}</h3><p class="meta">PMID ${esc(p.pmid || 'unavailable')} · Stance unassessed · Applicability unknown</p>${p.passages.slice(0, audience === 'everyday' ? 1 : 2).map(v => `<blockquote><span class="source-label">Source excerpt · ${esc(v.section)}</span>${highlight(v.text.slice(0, 650), run.query)}${v.text.length > 650 ? '…' : ''}</blockquote>${sectionLink(p.id, v.id, 'Read in context ↗')}`).join('')}${audience !== 'everyday' ? `<details><summary>Study context & source-linked mentions</summary>${fieldsHTML(studies[p.id])}</details>` : ''}${audience === 'research' ? `<details><summary>Retrieval score ${p.score.toFixed(4)} · inspect contributions</summary><pre>${esc(JSON.stringify(p.score_components, null, 2))}</pre></details>` : ''}<div class="paperbottom"><p class="meta">${p.rank}. Ranked for relevance</p><label><input type="checkbox" class="selectpaper" value="${esc(p.id)}" ${selected.has(p.id) ? 'checked' : ''}> Compare study</label></div></article>`).join('') : '<div class="empty">Try a more specific food and outcome, or broaden your filters. Absence from this collection is not evidence that a claim is false.</div>'}</div><aside class="sidebar"><div class="sidecard"><h3>Conditions matter</h3><p>Look for the population, amount, timing and comparator before applying a finding.</p><ul><li>Association does not establish causation.</li><li>A null result does not prove no effect.</li><li>Reviews can include the same primary studies.</li></ul><small>Study counts are not votes for a claim.</small></div><div class="sidecard"><h3>Your investigation</h3><label for="notes">Private notes</label><textarea class="note" id="notes" placeholder="Keep observations and questions here. Avoid personal health identifiers."></textarea><button id="risbtn">Export citations (.ris)</button><small>Notes persist when you save an investigation.</small></div></aside></div><form id="followform" class="followup"><label class="sr" for="followquery">Follow-up conditions</label><input id="followquery" placeholder="Add a condition, e.g. healthy adults, afternoon, 100 mg" required><button>Explore follow-up</button></form>${audience === 'research' ? `<details open><summary>Reproducible retrieval trace</summary><pre>${esc(JSON.stringify(run.trace, null, 2))}</pre></details>` : ''}`;
    $('#comparebtn').onclick = compare;
    $('#savebtn').onclick = save;
    $('#exportbtn').onclick = () => download(snapshot(), 'evidenceatlas-investigation.json');
    $('#risbtn').onclick = () => { location.href = '/api/bibliography?ids=' + encodeURIComponent((selected.size ? [...selected] : run.results.map(x => x.id)).join(',')); };
    $('#followform').onsubmit = e => { e.preventDefault(); history.push({ query: current.query, corpus: current.trace.index.corpus }); $('#query').value = current.query + ' ' + $('#followquery').value; runSearch(); };
    document.querySelectorAll('.selectpaper').forEach(el => el.onchange = () => { el.checked ? selected.add(el.value) : selected.delete(el.value); $('#comparebtn').textContent = `Compare selected (${selected.size})`; });
    bindInspect($('#resultsarea'));
    const cardButton = document.createElement('button');
    cardButton.textContent = 'Export readable card';
    $('.resultshead .actions').append(cardButton);
    cardButton.onclick = () => { const lines = ['# EvidenceAtlas Food investigation', '', `Question: ${run.query}`, `Exported: ${new Date().toISOString()}`, `Corpus: ${run.trace.index.corpus}`, '', run.evidence.summary, run.evidence.coverage, '', 'This is a source investigation, not a validated claim verdict.']; for (const p of run.results) {
        lines.push('', `## ${p.title}`, `${p.availability}; ${p.species}; ${p.year || 'year unknown'}`, `Source: https://pubmed.ncbi.nlm.nih.gov/${p.pmid}/`, 'Stance: unassessed. Study applicability: unknown.');
        const passage = p.passages[0];
        if (passage)
            lines.push(`Section: ${passage.section}`, `Passage: ${passage.id}`, '', `> ${passage.text.replaceAll('\n', '\n> ')}`);
    } lines.push('', '## Private notes', $('#notes')?.value || '(none)'); download(lines.join('\n'), 'evidenceatlas-card.md', 'text/markdown'); };
    if (audience === 'research') {
        const panel = document.createElement('details');
        panel.innerHTML = '<summary>Experimental passage stance & alternative findings</summary><p class="meta">Use a declarative claim. This local model has not been validated on the food benchmark. Its labels do not establish study applicability or scientific certainty.</p><label for="stanceclaim">Claim to assess</label><textarea class="note" id="stanceclaim" maxlength="1000"></textarea><button type="button" id="analyzebtn">Analyze source passages</button><div id="analysisresult" role="status"></div>';
        $('#resultsarea').append(panel);
        $('#stanceclaim').value = run.query;
        $('#analyzebtn').onclick = async () => { const button = $('#analyzebtn'); button.disabled = true; $('#analysisresult').textContent = 'Searching alternative findings and running the local passage model…'; try {
            const data = await api('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ claim: $('#stanceclaim').value, filters: run.trace.filters || {} }) });
            current.experimental_analysis = data;
            $('#analysisresult').innerHTML = `<p class="notice">${esc(data.assessment)}</p><p class="meta">${data.counterevidence.additional.length} additional candidate papers from two bounded alternative-finding searches. These are not automatically counterevidence.</p>${data.predictions.map(x => { const p = data.sources.find(s => s.passage_id === x.passage_id); return `<div class="paper"><span class="tag">Model candidate: ${esc(x.candidate_stance)}</span><p class="meta">Applicability unknown · ${esc(p.section)}</p><blockquote>${esc(p.text.slice(0, 500))}${p.text.length > 500 ? '…' : ''}</blockquote>${sectionLink(p.paper_id, p.passage_id, 'Inspect full context')}<details><summary>Model provenance & uncalibrated scores</summary><pre>${esc(JSON.stringify(x, null, 2))}</pre></details></div>`; }).join('')}`;
            bindInspect($('#analysisresult'));
        }
        catch (e) {
            $('#analysisresult').textContent = e.message;
        }
        finally {
            button.disabled = false;
        } };
    }
}
function bindInspect(root) { root.querySelectorAll('.inspect').forEach(b => b.onclick = () => openSource(b.dataset.paper, b.dataset.passage)); }
async function runSearch() { const query = $('#query').value.trim(); if (!query)
    return; $('#searchbutton').disabled = true; status('Searching the local collection and locating source passages…'); const params = new URLSearchParams({ q: query, method: $('#method').value === 'hybrid_rerank' ? 'hybrid' : $('#method').value, rerank: String($('#method').value === 'hybrid_rerank'), fulltext: String($('#fulltext').checked), human: String($('#human').checked), expand: String($('#expand').checked), section: $('#section').value, year_min: $('#year_min').value }); try {
    current = await api('/api/search?' + params);
    selected = new Set();
    lastSession = null;
    render();
    status(`${current.results.length} papers retrieved · ${Math.round(current.trace.latency_ms)} ms retrieval · collection ${current.trace.index.corpus.slice(0, 10)}`);
}
catch (e) {
    status(e.message, true);
}
finally {
    $('#searchbutton').disabled = false;
} }
async function openSource(pid, passage) { const dialog = $('#source'); $('#sourcebody').innerHTML = '<p>Loading the source…</p>'; if (!dialog.open)
    dialog.showModal(); try {
    const p = await api('/api/papers/' + encodeURIComponent(pid));
    const full = p.metadata.fulltext;
    $('#sourcebody').innerHTML = `<div class="tags"><span class="tag">${esc(p.availability)}</span><span class="tag">${esc(p.species)}</span></div><h2>${esc(p.title)}</h2><p class="meta">${esc(p.metadata.source_record.authorString || 'Authors unavailable')} · ${esc(p.year)} · ${esc(p.metadata.source_record.journalInfo?.journal?.title || '')}</p><p><a target="_blank" rel="noopener noreferrer" href="https://pubmed.ncbi.nlm.nih.gov/${encodeURIComponent(p.pmid)}/">PubMed record ↗</a> ${p.pmcid ? ` · <a target="_blank" rel="noopener noreferrer" href="https://europepmc.org/articles/${encodeURIComponent(p.pmcid)}">Publisher-deposited full text ↗</a>` : ''}</p><details><summary>Provenance, license & publication status</summary><p class="meta">Fetched ${esc(p.updated)}. Status coverage may be incomplete. Overlapping studies: ${esc(p.metadata.overlap)}.</p><pre>${esc(JSON.stringify({ license: full.licenses || 'Not available for abstract-only source', parser: full.parser, source_sha256: p.metadata.source_sha256, status: p.metadata.status_check, parsing_limits: full.limitations }, null, 2))}</pre></details><nav class="source-nav" aria-label="Article sections">${[...new Map(p.passages.map(v => [v.section, v])).values()].map(v => `<a href="#${esc(v.id)}">${esc(v.section)}</a>`).join('')}</nav>${p.passages.map(v => `<section id="${esc(v.id)}" class="sourcepassage ${v.id === passage ? 'highlighted' : ''}"><h3>${esc(v.section)} <span class="meta">· ${esc(v.zone)}</span></h3><p>${highlight(v.text, current?.query)}</p>${v.gaps?.length ? `<p class="notice">${esc(v.gaps.join('; '))}</p>` : ''}<details><summary>Stable passage and offsets</summary><pre>${esc(JSON.stringify({ id: v.id, section_id: v.section_id, start: v.start, end: v.end, xml_id: v.xml_id }, null, 2))}</pre></details></section>`).join('')}`;
    if (passage)
        setTimeout(() => document.getElementById(passage)?.scrollIntoView({ block: 'center' }), 30);
}
catch (e) {
    $('#sourcebody').textContent = e.message;
} }
async function compare() { if (selected.size < 2) {
    status('Select at least two studies to compare.', true);
    return;
} const ids = [...selected].slice(0, 4); const dialog = $('#compare'); $('#comparebody').innerHTML = '<p>Loading source-linked study contexts…</p>'; dialog.showModal(); try {
    const papers = await Promise.all(ids.map(id => api('/api/papers/' + encodeURIComponent(id))));
    const rows = ['food_identity', 'population', 'baseline_status', 'dose', 'frequency', 'timing', 'duration', 'preparation', 'comparator', 'substitution', 'outcome', 'design', 'effect_measure', 'limitations'];
    $('#comparebody').innerHTML = `<p class="notice">Mentions below are extracted candidates, not validated study characteristics. Compatibility and stance remain separate and unassessed. Comparing up to four selected papers.</p><table><thead><tr><th>Study context</th>${papers.map(p => `<th>${sectionLink(p.id, null, p.title)}<p>${esc(p.availability)}</p></th>`).join('')}</tr></thead><tbody>${rows.map(field => `<tr><th>${field}</th>${papers.map(p => `<td>${p.fields[field]?.length ? p.fields[field].slice(0, 3).map(v => sectionLink(p.id, v.passage_id, v.value)).join('<br>') : 'Unknown / not extracted'}</td>`).join('')}</tr>`).join('')}<tr><th>Stance</th>${papers.map(() => '<td>Unassessed</td>').join('')}</tr><tr><th>Compatibility</th>${papers.map(() => '<td>Unknown; review source context</td>').join('')}</tr></tbody></table>`;
    bindInspect($('#comparebody'));
}
catch (e) {
    $('#comparebody').textContent = e.message;
} }
async function save() { try {
    const r = await api('/api/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(snapshot()) });
    lastSession = r.id;
    status('Investigation and notes saved locally.');
}
catch (e) {
    status(e.message, true);
} }
async function saved() { const root = $('#savedlist'); root.textContent = 'Loading saved investigations…'; try {
    const sessions = await api('/api/sessions');
    root.innerHTML = sessions.length ? sessions.map(s => `<article class="paper"><h3>${esc(s.query)}</h3><p class="meta">Saved ${esc(new Date(s.created).toLocaleString())}</p><button class="loadsession" data-id="${esc(s.id)}">Open investigation</button> <a href="/api/sessions/${encodeURIComponent(s.id)}/export">Export JSON</a></article>`).join('') : '<div class="empty">No saved investigations yet. Explore a question, add notes, then choose Save investigation.</div>';
    root.querySelectorAll('.loadsession').forEach(b => b.onclick = async () => { const s = await api('/api/sessions/' + b.dataset.id); current = s.run; selected = new Set(s.selected || []); history = s.history || []; $('#query').value = s.query; page('explore'); render(); $('#notes').value = s.notes || ''; status('Loaded saved results. This preserves the collection version used at the time of search.'); });
}
catch (e) {
    root.textContent = e.message;
} }
function aiAuditPanel(a) {
    if (!a)
        return '';
    const relevant = Number(a.relevance_grade_counts['2'] || 0) + Number(a.relevance_grade_counts['3'] || 0);
    return `<section id="ai-audit" class="notice"><h3>Preliminary AI relevance audit</h3><p>${relevant}/${a.sample_pairs} retrieved papers were judged directly or nearly relevant; ${a.relevance_grade_counts['3']}/${a.sample_pairs} were judged directly applicable. This is not overall fact-checking accuracy.</p><p class="meta">Four development claims, top three results per claim, one AI reviewer who also built the system. Both directly applicable results are review discussions. No independent human validation. ${a.matches_current_dense_index ? 'The audit matches the current paper-level index.' : a.matches_current_corpus ? 'Historical paper-level audit: the corpus matches, but the active semantic index differs.' : 'Historical audit: the current corpus differs.'}</p><details><summary>Per-claim judgments and audit limits</summary><table><thead><tr><th>Claim</th><th>Relevant / 3</th><th>Applicable / 3</th></tr></thead><tbody>${a.results.map(r => `<tr><td>${esc(r.claim)}</td><td>${r.relevant_at_3}</td><td>${r.grade3_at_3}</td></tr>`).join('')}</tbody></table><p class="meta">Six relevant results had different or unclear conditions; four were related/background only. Context matching is an open issue. Held-out performance and stance accuracy remain unmeasured.</p><pre>${esc(JSON.stringify({ corpus: a.corpus, selection: a.selection, unmeasured: a.unmeasured }, null, 2))}</pre></details></section>`;
}
function denseIndexPanel(d) {
    if (!d)
        return '<p>Semantic index not built.</p>';
    const passage = d.level === 'passage';
    const n = passage ? d.passages : d.papers;
    const truncated = passage ? d.truncated_passages : d.truncated_inputs;
    return `<section id="dense-index"><h2>Active semantic index</h2><p><b>${number(n)} ${passage ? 'section passages' : 'title/abstract records'}</b> · ${d.dimensions} dimensions · ${d.max_tokens} model tokens per input.</p><p class="meta">${number(truncated)} inputs exceed the model limit and are truncated for embedding. Complete paragraphs remain available to lexical search and source inspection. ${passage ? 'Results link to the actual semantic-match passage.' : 'Displayed passages are chosen by term overlap after paper-level retrieval.'} This changes retrieval coverage, not scientific certainty.</p></section>`;
}
async function coverage() { const root = $('#coveragebody'); root.textContent = 'Measuring the collection…'; try {
    const [data, evaluation] = await Promise.all([api('/api/coverage'), api('/api/evaluation')]);
    root.innerHTML = `<div class="stats"><div class="stat"><b>${number(data.counts.papers)}</b><span>Unique metadata records</span></div><div class="stat"><b>${number(data.counts.availability['full-text'])}</b><span>Parsed full texts</span></div><div class="stat"><b>${number(data.counts.passages)}</b><span>Source passages</span></div><div class="stat"><b>${(data.storage.project_bytes / 1e9).toFixed(2)} GB</b><span>Project storage / ${(data.storage.budget_bytes / 1e9).toFixed(0)} GB budget</span></div></div><div class="notice"><h2>Coverage is a property of this collection</h2><p>${esc(data.limitations.join('. '))}.</p></div>${denseIndexPanel(data.dense_index)}<h2>Topic coverage</h2><table><thead><tr><th>Topic</th><th>Screening status</th><th>Unique records</th></tr></thead><tbody>${data.counts.topics.map(t => `<tr><td>${esc(t.topic.replaceAll('_', ' '))}</td><td>${esc(t.decision)}</td><td>${number(t.papers)}</td></tr>`).join('')}</tbody></table><p class="meta">A paper can appear in multiple topics. Screening decisions are provisional. ${data.counts.failures} unresolved acquisition failures.</p><h2>Evaluation</h2><p>${esc(evaluation.metrics_status)}. ${evaluation.human_judgments} human judgments recorded.</p><p>Runtime experiments are saved separately from effectiveness metrics. No expert validation or calibrated certainty is claimed.</p>${aiAuditPanel(evaluation.ai_audit)}<h3>Frozen development experiments</h3>${evaluation.experiments.map(e => `<details><summary>${esc(e.name)} · ${e.claims} queries · ${e.methods.length} methods</summary><p>${esc(e.quality_metrics)}. ${e.pool_candidates} pooled candidates.</p><table><thead><tr><th>Method</th><th>Median retrieval (ms)</th><th>Queries</th></tr></thead><tbody>${Object.entries(e.latencies_ms).map(([m, values]) => { const v = [...values].sort((a, b) => a - b); const median = (v[Math.floor((v.length - 1) / 2)] + v[Math.floor(v.length / 2)]) / 2; return `<tr><td>${esc(m)}</td><td>${Math.round(median)}</td><td>${v.length}</td></tr>`; }).join('')}</tbody></table><p class="meta">Single ordered development pass on local CPU, including cold model loads; not a load test or evidence of accuracy.</p></details>`).join('')}<details><summary>Acquisition jobs and corpus configuration</summary><pre>${esc(JSON.stringify({ index: data.index, jobs: data.jobs, storage: data.storage, experiments: evaluation.experiments }, null, 2))}</pre></details>`;
}
catch (e) {
    root.textContent = e.message;
} }
function page(id) { document.querySelectorAll('.page').forEach(el => el.hidden = el.id !== id); document.querySelectorAll('.nav').forEach(b => { const active = b.dataset.page === id; b.classList.toggle('active', active); if (active)
    b.setAttribute('aria-current', 'page');
else
    b.removeAttribute('aria-current'); }); if (id === 'saved')
    saved(); if (id === 'coverage')
    coverage(); }
document.querySelectorAll('.nav').forEach(b => b.onclick = () => page(b.dataset.page));
$('#searchform').onsubmit = e => { e.preventDefault(); history = []; runSearch(); };
document.querySelectorAll('[data-example]').forEach(b => b.onclick = () => { $('#query').value = b.dataset.example; history = []; runSearch(); });
document.querySelectorAll('[data-audience]').forEach(b => b.onclick = () => { const notes = $('#notes')?.value; audience = b.dataset.audience; document.querySelectorAll('[data-audience]').forEach(x => { x.classList.toggle('selected', x === b); x.setAttribute('aria-pressed', String(x === b)); }); render(); if ($('#notes') && notes)
    $('#notes').value = notes; });
$('#filtertoggle').onclick = () => { const filters = $('#filters'); filters.hidden = !filters.hidden; $('#filtertoggle').setAttribute('aria-expanded', String(!filters.hidden)); };
$('#closesource').onclick = () => $('#source').close();
$('#closecompare').onclick = () => $('#compare').close();
api('/api/coverage').then(d => { $('#overviewpapers').textContent = number(d.counts.searchable_papers); $('#overviewfulltexts').textContent = number(d.counts.availability['full-text']); $('#overviewpassages').textContent = number(d.counts.passages); $('#connectionstatus').textContent = 'Connected to your collection'; $('#smallcoverage').textContent = `${number(d.counts.papers)} records · ${number(d.counts.availability['full-text'])} full texts`; if (d.capabilities?.dense) {
    for (const [value, label] of [['dense', d.dense_index?.level === 'passage' ? 'Semantic (full-text passages)' : 'Semantic (title + abstract)'], ['hybrid', 'Hybrid (full text + semantic)'], ['hybrid_rerank', 'Hybrid + relevance reranking']]) {
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        $('#method').append(option);
    }
} }).catch(() => { $('#smallcoverage').textContent = 'Collection unavailable'; $('#connectionstatus').textContent = 'Collection unavailable'; });
export {};
