"""Loopback-only, on-demand GPU inference. No cloud endpoint or paid API."""
import json
import os
import re
import secrets
import subprocess
import threading
import time
from pathlib import Path

import requests

CONTEXT = 8192
MODEL_ALIAS = "evidenceatlas-summary"


class LocalLLM:
    def __init__(self, settings):
        self.settings = settings
        self.base = "http://127.0.0.1:" + str(int(os.environ.get("EAF_SUMMARY_PORT", "8766")))
        self.lock = threading.Lock()
        self.process = None
        self.session = requests.Session()
        self.session.trust_env = False

    def manifest(self):
        path = self.settings.root / "data/manifests/model-summarizer.json"
        if not path.exists():
            raise RuntimeError("Local summary model is not installed. See the README setup instructions.")
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("model_path", "runtime_path"):
            if not Path(data[key]).is_file():
                raise RuntimeError("Local summary model/runtime is missing. Run the model setup script.")
        return data

    def ensure(self):
        with self.lock:
            manifest = self.manifest()
            key_path = self.settings.root / "data/manifests/summarizer-key.txt"
            if not key_path.exists():
                key_path.write_text(secrets.token_urlsafe(32), encoding="utf-8")
            self.session.headers["Authorization"] = "Bearer " + key_path.read_text(encoding="utf-8").strip()
            try:
                r = self.session.get(self.base + "/v1/models", timeout=3)
                if r.status_code == 200 and any(x["id"] == MODEL_ALIAS for x in r.json().get("data", [])):
                    return
                if r.status_code != 503:
                    raise RuntimeError("The local summary port is occupied by a different service.")
            except requests.ConnectionError:
                log_path = self.settings.root / "tmp/local-summary-runtime.log"
                device = os.environ.get("EAF_SUMMARY_DEVICE")
                if not device:
                    devices = subprocess.run([manifest["runtime_path"], "--list-devices"],
                        capture_output=True, text=True, timeout=30,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                    match = re.search(r"(Vulkan\d+):[^\n]*NVIDIA", devices.stdout + devices.stderr)
                    if not match:
                        raise RuntimeError("No NVIDIA Vulkan device found. Set EAF_SUMMARY_DEVICE to a supported device.")
                    device = match.group(1)
                args = [manifest["runtime_path"], "-m", manifest["model_path"],
                        "--alias", MODEL_ALIAS, "--host", "127.0.0.1",
                        "--port", self.base.rsplit(":", 1)[1], "-c", str(CONTEXT),
                        "--device", device, "-ngl", "99", "-t", "4", "-b", "512", "-ub", "128",
                        "--parallel", "1", "--no-webui", "--no-context-shift",
                        "--sleep-idle-seconds", "120", "--api-key-file", str(key_path)]
                with log_path.open("ab") as log:
                    self.process = subprocess.Popen(args, cwd=Path(manifest["runtime_path"]).parent,
                        stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            for _ in range(180):
                if self.process is not None and self.process.poll() is not None:
                    raise RuntimeError("Local model could not start. Check tmp/local-summary-runtime.log.")
                try:
                    response = self.session.get(self.base + "/health", timeout=2)
                    if response.status_code == 200:
                        return
                except requests.RequestException:
                    pass
                time.sleep(1)
            raise RuntimeError("Local model startup timed out; check available memory and the runtime log.")

    def tokens(self, text):
        response = self.session.post(self.base + "/tokenize",
            json={"content": text, "add_special": False, "parse_special": False}, timeout=180)
        response.raise_for_status()
        return len(response.json()["tokens"])

    def generate(self, system, user, schema, max_tokens=650):
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        # Count the actual chat template; never let the runtime silently drop source text.
        template = self.session.post(self.base + "/apply-template",
            json={"messages": messages, "add_generation_prompt": True}, timeout=180)
        template.raise_for_status()
        prompt = template.json()["prompt"]
        if self.tokens(prompt) + max_tokens > CONTEXT:
            raise ValueError("Summary input exceeds the local context window; no text was silently truncated.")
        response = self.session.post(self.base + "/v1/chat/completions", json={
            "model": MODEL_ALIAS, "messages": messages, "temperature": 0, "seed": 42,
            "max_tokens": max_tokens, "stream": False, "cache_prompt": True,
            "response_format": {"type": "json_schema", "json_schema":
                {"name": "evidence", "strict": True, "schema": schema}}}, timeout=300)
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]
        if choice["finish_reason"] != "stop":
            raise RuntimeError("The model reached its output limit; an incomplete answer was not displayed.")
        value = json.loads(choice["message"]["content"])
        if not isinstance(value, dict):
            raise ValueError("The local model returned an invalid structured answer.")
        return value, data.get("usage", {})
