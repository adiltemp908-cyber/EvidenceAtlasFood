from __future__ import annotations
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    root: Path
    budget_bytes: int = 160_000_000_000
    reserve_bytes: int = 40_000_000_000
    request_interval: float = 1.0
    cutoff: str = "2026-10-06"
    since: str = "1900-01-01"

    @classmethod
    def load(cls):
        return cls(Path(os.environ.get("EAF_ROOT", "E:/EvidenceAtlasFood")).resolve(),
                   int(os.environ.get("EAF_BUDGET_BYTES", 160_000_000_000)),
                   int(os.environ.get("EAF_RESERVE_BYTES", 40_000_000_000)))

    def initialize(self):
        if os.name == "nt" and self.root.drive.lower() == "c:":
            raise ValueError("Bulk storage on C: is disabled. Set EAF_ROOT to an authorized data volume.")
        self.root.mkdir(parents=True, exist_ok=True)
        self.check_space()
        for name in ("data/raw", "data/normalized", "data/manifests", "indexes", "models", "cache", "experiments", "tmp"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        for key, value in {"HF_HOME":"cache/huggingface", "SENTENCE_TRANSFORMERS_HOME":"models", "TORCH_HOME":"cache/torch", "TMP":"tmp", "TEMP":"tmp"}.items():
            os.environ[key] = str(self.root/value)
        self.atomic_json(self.root/"data/manifests/storage-config.json", self.report())

    def usage(self):
        return sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file()) if self.root.exists() else 0

    def check_space(self, additional=0, rebuild=0):
        free = shutil.disk_usage(self.root if self.root.exists() else self.root.anchor).free
        used = self.usage()
        required = additional + rebuild
        if used+required > self.budget_bytes or free-required < self.reserve_bytes:
            raise OSError(f"Storage guard: used={used}, free={free}, required={required}; budget/reserve would be exceeded")

    def report(self):
        return {"root":str(self.root), "project_bytes":self.usage(), "free_bytes":shutil.disk_usage(self.root).free,
                "budget_bytes":self.budget_bytes, "reserve_bytes":self.reserve_bytes}

    @staticmethod
    def atomic_json(path, value):
        tmp = path.with_suffix(path.suffix+".part")
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
