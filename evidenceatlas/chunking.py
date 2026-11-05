"""Token-bounded semantic windows; source passages and their IDs stay intact."""
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

from .config import Settings
from .models import MODELS, embedding_model
from .store import Store

VERSION = "token-windows-v1"
OVERLAP = 32


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_spans(text, tokenizer, max_tokens=256, overlap=OVERLAP):
    """Return exact character spans, including all text, without decoding tokens."""
    budget = max_tokens - tokenizer.num_special_tokens_to_add(pair=False)
    if not 0 <= overlap < budget:
        raise ValueError("Overlap must be smaller than the content-token budget")
    encoded = tokenizer(text, add_special_tokens=False, truncation=False,
                        return_offsets_mapping=True)
    offsets = encoded["offset_mapping"]
    if len(offsets) <= budget:
        return [(0, len(text))]
    spans = []
    start = 0
    while start < len(offsets):
        end = min(start + budget, len(offsets))
        lo = 0 if start == 0 else offsets[start][0]
        hi = len(text) if end == len(offsets) else offsets[end][0]
        # A substring starting inside a word can tokenize differently. Verify
        # the actual encoder input rather than trusting original token counts.
        while len(tokenizer.encode(text[lo:hi], add_special_tokens=True,
                                   truncation=False)) > max_tokens:
            end -= 1
            if end <= start:
                raise ValueError("Cannot fit source span inside model limit")
            hi = offsets[end][0]
        spans.append((lo, hi))
        if end == len(offsets):
            break
        start = max(start + 1, end - overlap)
    assert spans[0][0] == 0 and spans[-1][1] == len(text)
    assert all(b[0] <= a[1] for a, b in zip(spans, spans[1:]))
    return spans


def build_chunked(store, settings, baseline_path=None, previous_directory=None, batch_size=8):
    """Stage a resumable index; reuse only verified identical encoder inputs."""
    from .dense import validate_vectors
    started = time.perf_counter()
    model = embedding_model(settings)
    if not model.tokenizer.is_fast:
        raise ValueError("Source offsets require a fast tokenizer")
    corpus = store.fingerprint()
    directory = settings.root / "indexes" / ("dense-" + corpus[:16] + "-chunks-v1")
    directory.mkdir(parents=True, exist_ok=True)
    identity = dict(corpus=corpus, model=list(MODELS["embedding"]),
                    max_tokens=model.max_seq_length, chunking=VERSION, overlap_tokens=OVERLAP)
    old_vectors = None
    reusable = {}
    if previous_directory:
        previous_directory = Path(previous_directory)
        old = json.loads((previous_directory / "manifest.json").read_text())
        if old["model"] != identity["model"] or old["max_tokens"] != model.max_seq_length or old.get("level") != "passage":
            raise ValueError("Source model/limit/level does not match")
        baseline = Store(baseline_path)
        if baseline.fingerprint() != old["corpus"]:
            raise ValueError("Baseline corpus does not match source vectors")
        old_vectors = np.load(previous_directory / "vectors.npy", mmap_mode="r")
        validate_vectors(old_vectors, len(old["ids"]))
        positions = defaultdict(list)
        for i, meta in enumerate(old["ids"]):
            positions[meta["id"]].append((i, meta))
        for row in baseline.db.execute("SELECT id,text FROM passages ORDER BY id"):
            for i, meta in positions.get(row["id"], []):
                text = row["text"][meta.get("char_start", 0):meta.get("char_end", len(row["text"]))]
                sha = digest(text)
                if meta.get("text_sha256", sha) != sha:
                    raise ValueError("Source chunk content does not match manifest")
                reusable[(row["id"], sha)] = i
        baseline.db.close()
        identity["source_corpus"] = old["corpus"]
    if (directory / "manifest.json").exists():
        done = json.loads((directory / "manifest.json").read_text())
        if any(done.get(k) != v for k, v in identity.items() if k != "source_corpus"):
            raise ValueError("Existing completed index has incompatible settings")
        validate_vectors(np.load(directory / "vectors.npy", mmap_mode="r"), len(done["ids"]))
        return {k: v for k, v in done.items() if k != "ids"}
    ids = []
    parents = split_parents = 0
    for row in store.db.execute("SELECT id,paper_id,zone,text FROM passages ORDER BY id"):
        spans = split_spans(row["text"], model.tokenizer, model.max_seq_length)
        parents += 1
        split_parents += len(spans) > 1
        for lo, hi in spans:
            ids.append(dict(id=row["id"], paper_id=row["paper_id"], zone=row["zone"],
                            char_start=lo, char_end=hi, text_sha256=digest(row["text"][lo:hi])))
    settings.check_space(additional=len(ids) * 384 * 8)
    progress_path = directory / "incremental-progress.json"
    part = directory / "vectors.part.npy"
    state = json.loads(progress_path.read_text()) if progress_path.exists() else {}
    if part.exists() and (any(state.get(k) != v for k, v in identity.items()) or state.get("total") != len(ids)):
        raise ValueError("Checkpoint does not match current chunk plan")
    offset = state.get("completed", 0) if part.exists() else 0
    if not 0 <= offset <= len(ids):
        raise ValueError("Invalid checkpoint offset")
    reused = state.get("reused", 0) if offset else 0
    encoded = state.get("encoded_new", 0) if offset else 0
    vectors = np.lib.format.open_memmap(part, mode="r+" if part.exists() else "w+",
                                       dtype="float32", shape=(len(ids), 384))
    while offset < len(ids):
        batch = ids[offset:offset + 64]
        missing, destinations = [], []
        for j, meta in enumerate(batch):
            old_index = reusable.get((meta["id"], meta["text_sha256"]))
            if old_index is not None:
                vectors[offset + j] = old_vectors[old_index]
                reused += 1
            else:
                text = store.db.execute("SELECT text FROM passages WHERE id=?", (meta["id"],)).fetchone()[0]
                text = text[meta["char_start"]:meta["char_end"]]
                if digest(text) != meta["text_sha256"]:
                    raise ValueError("Source text changed during build")
                missing.append(text)
                destinations.append(offset + j)
        if missing:
            vectors[destinations] = model.encode(missing, batch_size=batch_size,
                                                 normalize_embeddings=True, show_progress_bar=False)
            encoded += len(missing)
        offset += len(batch)
        if offset % 256 == 0 or offset == len(ids):
            vectors.flush()
            state = dict(identity, completed=offset, total=len(ids), reused=reused,
                         encoded_new=encoded, elapsed_seconds=time.perf_counter() - started)
            Settings.atomic_json(progress_path, state)
            print(json.dumps(state), flush=True)
    validation = validate_vectors(vectors, len(ids))
    if store.fingerprint() != corpus:
        raise ValueError("Corpus changed during encoding")
    vectors.flush()
    del vectors
    part.replace(directory / "vectors.npy")
    meta = dict(identity, level="passage", input="overlapping token-bounded source spans; exact character offsets",
                dimensions=384, passages=len(ids), source_passages=parents, split_passages=split_parents,
                truncated_passages=0, reused_vectors=reused, new_vectors=encoded,
                elapsed_seconds=time.perf_counter() - started, validation=validation,
                ids=ids, path=str(directory))
    Settings.atomic_json(directory / "manifest.json", meta)
    return {k: v for k, v in meta.items() if k != "ids"}
