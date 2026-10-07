"""Open the local interface, starting the server only when it is not already running."""
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen
import json
import webbrowser

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8765'

def ready():
    try:
        with urlopen(URL+'/api/health',timeout=1) as response:
            data=json.load(response)
            return data.get('status')=='ok' and data.get('version')=='0.1.0'
    except (OSError,ValueError):return False

def main():
    if ready():webbrowser.open(URL);return 0
    data=Path(os.environ.get('EAF_ROOT','E:/EvidenceAtlasFood'))
    if not (data/'data/normalized/corpus.sqlite').is_file():
        print('The literature collection is missing. Set EAF_ROOT to your existing data folder; see README.md.');return 1
    data.joinpath('tmp').mkdir(exist_ok=True)
    log_path=data/'tmp/interface-launch.log'
    with log_path.open('ab') as log:
        process=subprocess.Popen([sys.executable,'-m','evidenceatlas.cli','serve','--port','8765'],cwd=ROOT,
            stdout=log,stderr=log,stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    for _ in range(40):
        if ready():webbrowser.open(URL);return 0
        if process.poll() is not None:break
        time.sleep(.5)
    print(f'The interface could not start. Check {log_path} and the setup instructions in README.md.');return 1

if __name__=='__main__':raise SystemExit(main())
