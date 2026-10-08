from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True, slots=True)
class LabPaths:
    root: Path
    @classmethod
    def from_env(cls):
        raw=os.environ.get("EZSTUDIO_RUNTIME_ROOT")
        return cls(Path(raw) if raw else Path(r"H:\temp\EZStudio_lab"))
    @property
    def artifacts(self): return self.root/"artifacts"
    @property
    def runs(self): return self.root/"runs"
    @property
    def cache(self): return self.root/"cache"
    @property
    def exports(self): return self.root/"exports"
    @property
    def logs(self): return self.root/"logs"
    def ensure(self):
        for p in (self.root,self.artifacts,self.runs,self.cache,self.exports,self.logs): p.mkdir(parents=True,exist_ok=True)
