from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import copy,yaml

STATE_DIR=".mvp-os"; STATE_FILE="state.yml"
DEFAULT_STATE={
 "schema_version":1,
 "project":{"name":None,"description":None},
 "lifecycle":{"current_gate":"G0","status":"active","next_action":"Define the project context and initial idea."},
 "problem":{"user":None,"problem":None},
 "hypotheses":[],"experiments":[],"evidence":[],"learnings":[],"decisions":[],
 "mvp":{"scope":[],"out_of_scope":[]},
 "sdd":{"provider":"none","status":"not_started"},
}
@dataclass
class ProjectState:
 root: Path
 @property
 def directory(self): return self.root/STATE_DIR
 @property
 def path(self): return self.directory/STATE_FILE
 def exists(self): return self.path.exists()
 def load(self)->dict[str,Any]:
  return yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
 def save(self,data): self.directory.mkdir(parents=True,exist_ok=True); self.path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding="utf-8")
 def init(self,name=None,description=None,provider="none"):
  if self.exists(): return False
  d=copy.deepcopy(DEFAULT_STATE); d["project"]["name"]=name; d["project"]["description"]=description; d["sdd"]["provider"]=provider; self.save(d); return True
def detect_spec_kit(root): return (root/".specify").exists() or (root/"specify.yml").exists()
