"""Build a source-only delivery with per-file hashes; no data-volume or private notes."""
from pathlib import Path
import hashlib,json,zipfile

root=Path(__file__).resolve().parents[1]
folders=('evidenceatlas','web','tests','scripts','docs','evaluation')
suffixes={'.py','.ts','.js','.html','.css','.svg','.md','.json','.jsonl','.txt','.pdf','.png'}
files=[root/n for n in ('README.md','run.ps1','Open EvidenceAtlas.cmd','requirements.txt','requirements-models.txt','tsconfig.json','.env.example','.gitignore')]
for folder in folders:
    files.extend(p for p in (root/folder).rglob('*') if p.is_file() and p.suffix in suffixes and '__pycache__' not in p.parts)
files=sorted(set(files));manifest={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
release=root/'releases';release.mkdir(exist_ok=True)
archive=release/'EvidenceAtlasFood-source.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,'EvidenceAtlasFood/'+p.relative_to(root).as_posix())
    z.writestr('EvidenceAtlasFood/SOURCE_MANIFEST.json',json.dumps(manifest,indent=2))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for path,digest in manifest.items():assert hashlib.sha256(z.read('EvidenceAtlasFood/'+path)).hexdigest()==digest
print(json.dumps({'archive':str(archive),'files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'excludes':'E: corpus/models/caches, private sessions, .git, local .env'},indent=2))
