from __future__ import annotations

GATES = {
    "G0": "Intake", "G1": "Problem / User", "G2": "Hypotheses",
    "G3": "Validation Strategy", "G4": "Product Definition",
    "G5": "SDD / Technical Definition", "G6": "MVP Readiness",
    "G7": "MVP Validation", "G8": "Learning / Decision",
}
TRANSITIONS = {
    "G0": {"G1"}, "G1": {"G0","G2"}, "G2": {"G1","G3"},
    "G3": {"G2","G4"}, "G4": {"G3","G5"}, "G5": {"G4","G6"},
    "G6": {"G5","G7"}, "G7": {"G6","G8","G2","G3","G4"},
    "G8": {"G2","G3","G4","G5","G6","G7"},
}
def gate_name(gate): return GATES.get(gate,"Unknown")
def is_valid_gate(gate): return gate in GATES
def transition_allowed(current,target): return target in TRANSITIONS.get(current,set())

def gate_requirements_satisfied(data,target):
    errors=[]
    p=data.get("project",{}); problem=data.get("problem",{})
    hs=data.get("hypotheses",[]); exps=data.get("experiments",[])
    evidence=data.get("evidence",[]); learnings=data.get("learnings",[])
    decisions=data.get("decisions",[]); mvp=data.get("mvp",{})
    sdd=data.get("sdd",{})
    if target=="G1":
        if not p.get("description"): errors.append("project.description is required")
        if not problem.get("user"): errors.append("problem.user is required")
    elif target=="G2":
        if not problem.get("user"): errors.append("problem.user is required")
        if not problem.get("problem"): errors.append("problem.problem is required")
    elif target=="G3":
        if not hs: errors.append("at least one hypothesis is required")
        for i,h in enumerate(hs):
            if not isinstance(h,dict): errors.append(f"hypotheses[{i}] must be a mapping"); continue
            for f in ("id","statement","risk","test","success_metric"):
                if not h.get(f): errors.append(f"hypotheses[{i}].{f} is required")
    elif target=="G4":
        if not hs: errors.append("at least one hypothesis is required")
        if not exps: errors.append("at least one validation experiment is required")
    elif target=="G5":
        if not mvp.get("scope"): errors.append("mvp.scope must be defined")
        if sdd.get("provider")=="none" and sdd.get("status")!="not_required":
            errors.append("without an SDD provider, set sdd.status to 'not_required'")
    elif target=="G6":
        if not mvp.get("scope"): errors.append("mvp.scope must be defined")
        if sdd.get("provider")!="none" and sdd.get("status") not in {"ready","active"}:
            errors.append("SDD provider must be ready or active")
    elif target=="G7":
        if not mvp.get("scope"): errors.append("mvp.scope must be defined")
        if not decisions and not evidence: errors.append("evidence or an explicit decision is required before MVP validation")
    elif target=="G8":
        if not evidence: errors.append("at least one evidence item is required")
        if not learnings: errors.append("at least one learning is required")
        if not decisions: errors.append("at least one decision is required")
    return errors
