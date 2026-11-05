"""Complement a staged everyday-diet batch with reviews and reference-value papers."""
import argparse
from dataclasses import replace
from datetime import date
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidenceatlas.acquisition import EuropePMC, ingest, now
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.taxonomy import EVERYDAY_TOPICS, TOPICS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--cutoff', required=True, type=date.fromisoformat)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--page-size', type=int, default=5)
    args = parser.parse_args()
    if args.seconds <= 0 or not 1 <= args.page_size <= 100:
        parser.error('Use positive seconds and page size 1–100')
    settings = Settings.load()
    settings.initialize()
    folder = settings.root / 'experiments' / args.run
    state = json.loads((folder / 'status.json').read_text())
    if state['status'] != 'acquired-awaiting-indexes':
        raise ValueError('Complete initial acquisition; do not modify an indexed or live collection')
    marker = folder / 'everyday-review-acquisition.json'
    progress = json.loads(marker.read_text()) if marker.exists() else {
        'next_topic': 0, 'batches': [], 'errors': [], 'cutoff': args.cutoff.isoformat(),
        'page_size': args.page_size, 'topics': list(EVERYDAY_TOPICS), 'started_at': now()}
    if progress['cutoff'] != args.cutoff.isoformat() or progress['page_size'] != args.page_size:
        raise ValueError('Resume with the same cutoff and page size')
    # Keep existing topic labels; actual queries and cursors are stored by ingest.
    for topic in progress['topics']:
        mesh, words, terms = TOPICS[topic]
        TOPICS[topic] = (mesh, words + ' AND (review OR "meta-analysis" OR guideline OR recommendations OR "reference values")', terms)
    client = EuropePMC(replace(settings, since='2000-01-01', cutoff=args.cutoff.isoformat()))
    store = Store(folder / 'corpus.sqlite')
    started = time.monotonic()
    try:
        while progress['next_topic'] < len(progress['topics']) and time.monotonic() - started < args.seconds:
            topic = progress['topics'][progress['next_topic']]
            try:
                result = ingest(store, client, [topic], pages=1, page_size=args.page_size,
                                seconds=max(1, args.seconds - (time.monotonic() - started)))
                progress['batches'].append({'topic': topic, 'pages': result['pages'], 'finished_at': now()})
                print(json.dumps({'topic': topic, 'pages': result['pages']}), flush=True)
            except Exception as exc:
                progress['errors'].append({'topic': topic, 'error': str(exc)[:500]})
            progress['next_topic'] += 1
            Settings.atomic_json(marker, progress)
        progress.update(completed=progress['next_topic'] == len(progress['topics']),
                        elapsed_seconds=time.monotonic() - started, counts=store.counts())
        Settings.atomic_json(marker, progress)
        state.update(counts=store.counts(), corpus=store.fingerprint(), review_acquisition=str(marker))
        Settings.atomic_json(folder / 'status.json', state)
        print(json.dumps({'completed': progress['completed'], 'counts': state['counts']}), flush=True)
    finally:
        store.db.close()


if __name__ == '__main__':
    main()
