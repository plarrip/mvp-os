from __future__ import annotations
import argparse
from pathlib import Path
from importlib.resources import files
from .state import ProjectState,detect_spec_kit
from .lifecycle import GATES,gate_name,is_valid_gate,transition_allowed,gate_requirements_satisfied
from .validation import validate_state,validate_shape

def root(): return Path.cwd()

def write_agent_instructions(r):
 content="""# MVP-OS project instructions

This project uses MVP-OS as its default product-development operating system.

1. Read `.mvp-os/methodology.md` and `.mvp-os/state.yml`.
2. Work from the current gate and next action.
3. Prefer the smallest next action that can produce meaningful validated learning.
4. Do not write production code merely because an idea was mentioned.
5. Persist durable product state in `.mvp-os/state.yml`.
6. After meaningful state changes, run `mvp-os validate`.
7. To change gates, use `mvp-os transition <GATE>`; do not edit `lifecycle.current_gate` directly.
8. If evidence is insufficient, state `INSUFFICIENT EVIDENCE`, identify what is missing, and stop.
9. If an SDD provider is present, use it for technical specification rather than duplicating its primitives.

The agent owns product reasoning and content. MVP-OS owns deterministic state validation and gate transitions.
"""
 marker="<!-- MVP-OS instructions -->"; p=r/"AGENTS.md"; block=marker+"\n"+content
 if p.exists():
  s=p.read_text(encoding="utf-8")
  if marker not in s: p.write_text(s.rstrip()+"\n\n"+block+"\n",encoding="utf-8")
 else: p.write_text(block+"\n",encoding="utf-8")
 c=r/"CLAUDE.md"; w="@AGENTS.md\n"
 if not c.exists(): c.write_text(w,encoding="utf-8")
 elif "@AGENTS.md" not in c.read_text(encoding="utf-8"): c.write_text(c.read_text(encoding="utf-8").rstrip()+"\n\n"+w,encoding="utf-8")

def install_resources(r):
 notices=[]
 d=r/".mvp-os"; d.mkdir(parents=True,exist_ok=True)
 packaged=files("mvp_os.resources").joinpath("methodology.md").read_text(encoding="utf-8")
 methodology=d/"methodology.md"
 if not methodology.exists(): methodology.write_text(packaged,encoding="utf-8")
 elif methodology.read_text(encoding="utf-8")!=packaged:
  notices.append("Kept .mvp-os/methodology.md: it differs from the packaged version. Delete it and re-run init to take the packaged one.")
 g=r/".gitignore"; t=files("mvp_os.resources").joinpath("gitignore.template").read_text(encoding="utf-8")
 if not g.exists(): g.write_text(t,encoding="utf-8")
 elif ".venv/" not in g.read_text(encoding="utf-8"): g.write_text(g.read_text(encoding="utf-8").rstrip()+"\n.venv/\n",encoding="utf-8")
 return notices

def main():
 p=argparse.ArgumentParser(prog="mvp-os"); s=p.add_subparsers(dest="command",required=True)
 i=s.add_parser("init"); i.add_argument("--name"); i.add_argument("--description")
 t=s.add_parser("transition"); t.add_argument("target")
 for c in ("status","gate","next","review","validate"): s.add_parser(c)
 a=p.parse_args(); st=ProjectState(root())
 if a.command=="init":
  provider="spec-kit" if detect_spec_kit(root()) else "none"; created=st.init(a.name,a.description,provider); changed=[]
  if not created:
   d=st.load()
   if d.get("sdd",{}).get("provider")!=provider: d.setdefault("sdd",{})["provider"]=provider; changed.append(f"sdd.provider -> {provider}")
   for field,value in (("name",a.name),("description",a.description)):
    if value and isinstance(d.get("project"),dict) and d["project"].get(field)!=value:
     d["project"][field]=value; changed.append(f"project.{field} -> {value}")
   if changed: st.save(d)
  notices=install_resources(root()); write_agent_instructions(root())
  print("Initialized MVP-OS" if created else "MVP-OS already initialized"); print(f"SDD provider: {provider}")
  for c in changed: print(f"Updated {c}")
  for n in notices: print(n)
  return 0
 if not st.exists(): print("MVP-OS is not initialized. Run: mvp-os init"); return 1
 d=st.load()
 if a.command=="validate":
  e=validate_state(d)
  if e: print("INVALID"); [print("- "+x) for x in e]; return 1
  print("VALID"); return 0
 if a.command=="transition":
  target=a.target.upper(); current=d.get("lifecycle",{}).get("current_gate")
  if not is_valid_gate(target): print("REJECTED\n- unknown target gate: "+target); return 1
  structural=validate_state(d,False)
  if structural: print("REJECTED"); [print("- invalid state: "+x) for x in structural]; return 1
  if not transition_allowed(current,target): print(f"REJECTED\n- transition {current} → {target} is not allowed"); return 1
  req=gate_requirements_satisfied(d,target)
  if req: print("REJECTED"); [print("- "+x) for x in req]; return 1
  d["lifecycle"]["current_gate"]=target; d["lifecycle"]["next_action"]=None; st.save(d)
  print(f"ACCEPTED\n{current} → {target} — {gate_name(target)}")
  print("next_action cleared. Set it in .mvp-os/state.yml; validate will fail until you do.")
  return 0
 shape=validate_shape(d)
 if shape:
  print("UNREADABLE STATE — .mvp-os/state.yml cannot be parsed:")
  [print("- "+x) for x in shape]
  print("Fix the file, then run `mvp-os validate`.")
  return 1
 l=d.get("lifecycle",{}); g=l.get("current_gate","G0")
 if a.command=="status": print(f"Project: {d.get('project',{}).get('name') or '(unnamed)'}\nStatus: {l.get('status')}\nGate: {g} — {gate_name(g)}\nSDD: {d.get('sdd',{}).get('provider')}\nNext: {l.get('next_action') or '(not defined)'}")
 elif a.command=="gate": print(f"{g} — {gate_name(g)}")
 elif a.command=="next": print(l.get("next_action") or "No next action defined.")
 elif a.command=="review": print(f"Gate: {g} — {gate_name(g)}\nStatus: {l.get('status')}\nNext action: {l.get('next_action') or '(not defined)'}\nSDD provider: {d.get('sdd',{}).get('provider')}\nHypotheses: {len(d.get('hypotheses',[]))}\nExperiments: {len(d.get('experiments',[]))}\nEvidence items: {len(d.get('evidence',[]))}\nDecisions: {len(d.get('decisions',[]))}")
 return 0
if __name__=="__main__": raise SystemExit(main())
