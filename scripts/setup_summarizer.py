"""Download pinned local inference artifacts onto EAF_ROOT; no cloud inference."""
import hashlib
import sys
import time
import zipfile
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidenceatlas.config import Settings

MODEL_REVISION = "4edb920b6f14e3b9284d4502a6485103d72cde05"
MODEL_FILE = "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
MODEL_SHA = "8cdb57cbb880d313736a9bc4e3d3d2485f145b5e19cf33783746e753e82641fc"
RUNTIME_SHA = "d994930aa5739c77d14f34599e0b905ea86c04e53a6ba7ec94a317bbc5e0effd"


def checksum(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def download(url, destination, expected_size, expected_sha):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if checksum(destination) != expected_sha:
            raise ValueError(f"Existing file checksum differs: {destination}")
        return
    part = destination.with_suffix(destination.suffix + ".part")
    for attempt in range(6):
        try:
            offset = part.stat().st_size if part.exists() else 0
            if offset == expected_size:
                break
            with requests.get(url, headers={"Range": f"bytes={offset}-"} if offset else {},
                              stream=True, timeout=(30, 120)) as response:
                response.raise_for_status()
                if offset and response.status_code == 206:
                    if not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                        raise ValueError("Download resume range does not match")
                elif offset:
                    offset = 0
                with part.open("ab" if offset else "wb") as f:
                    last = time.monotonic()
                    for chunk in response.iter_content(4 * 1024 * 1024):
                        f.write(chunk)
                        offset += len(chunk)
                        if time.monotonic() - last > 15:
                            print(f"{destination.name}: {offset/expected_size:.0%}", flush=True)
                            last = time.monotonic()
            break
        except requests.RequestException:
            if attempt == 5:
                raise
            time.sleep(2 + attempt)
    if part.stat().st_size != expected_size or checksum(part) != expected_sha:
        raise ValueError(f"Downloaded artifact failed checksum validation: {part}")
    part.replace(destination)


def main():
    settings = Settings.load()
    settings.initialize()
    settings.check_space(additional=3_000_000_000)
    model = settings.root / "models/summarizer" / MODEL_FILE
    runtime = settings.root / "models/llama-b11753"
    runtime_url = "https://github.com/ggml-org/llama.cpp/releases/download/b11753/llama-b11753-bin-win-vulkan-x64.zip"
    model_url = f"https://huggingface.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF/resolve/{MODEL_REVISION}/{MODEL_FILE}"
    download(runtime_url, runtime / "runtime.zip", 36751562, RUNTIME_SHA)
    download(model_url, model, 2497280448, MODEL_SHA)
    if not list(runtime.rglob("llama-server.exe")):
        with zipfile.ZipFile(runtime / "runtime.zip") as archive:
            for name in archive.namelist():
                if not (runtime / name).resolve().is_relative_to(runtime.resolve()):
                    raise ValueError("Unsafe archive path")
            archive.extractall(runtime)
    Settings.atomic_json(settings.root / "data/manifests/model-summarizer.json", {
        "model": "Qwen3-4B-Instruct-2507", "quantization": "Q4_K_M",
        "model_path": str(model), "model_sha256": MODEL_SHA,
        "repository": "lmstudio-community/Qwen3-4B-Instruct-2507-GGUF", "revision": MODEL_REVISION,
        "runtime": "llama.cpp b11753 Vulkan", "runtime_path": str(next(runtime.rglob("llama-server.exe"))),
        "runtime_sha256": RUNTIME_SHA, "sources": [runtime_url, model_url],
        "original_model": "https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507",
        "license": "Apache-2.0 (model); MIT (llama.cpp)"})
    print("Local summarizer installed. It will load on demand when you click Summarize.")


if __name__ == "__main__":
    main()
