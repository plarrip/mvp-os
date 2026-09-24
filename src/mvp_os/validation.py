from __future__ import annotations
from .lifecycle import is_valid_gate, gate_requirements_satisfied

REQUIRED={"schema_version","project","lifecycle","problem","hypotheses","experiments","evidence","learnings","decisions","mvp","sdd"}

def validate_shape(data):
    """Type-level checks only: can the read commands parse this state at all?

    Kept separate from validate_state so the read commands can tell an
    unreadable state (refuse, point at validate) from a merely incomplete one
    (a cleared next_action after a transition is a normal working state).
    """
    if not isinstance(data,dict): return ["state root must be a mapping"]
    errors=[f"missing top-level field: {k}" for k in sorted(REQUIRED-set(data))]
    if data.get("schema_version")!=1: errors.append(f"unsupported schema_version: {data.get('schema_version')!r}")
    for k in ("project","lifecycle","problem","mvp","sdd"):
        if not isinstance(data.get(k),dict): errors.append(f"{k} must be a mapping")
    for k in ("hypotheses","experiments","evidence","learnings","decisions"):
        if not isinstance(data.get(k),list): errors.append(f"{k} must be a list")
    return errors

def validate_state(data, check_gate_requirements=True):
    errors=validate_shape(data)
    if not isinstance(data,dict): return errors
    l=data.get("lifecycle",{})
    if isinstance(l,dict):
        if not is_valid_gate(l.get("current_gate")): errors.append(f"invalid lifecycle.current_gate: {l.get('current_gate')!r}")
        if l.get("status") not in {"active","paused","stopped","completed"}: errors.append(f"invalid lifecycle.status: {l.get('status')!r}")
        if l.get("status")=="active" and not l.get("next_action"): errors.append("lifecycle.next_action is required while the project is active")
    for field in ("hypotheses","experiments","evidence","learnings","decisions"):
        if not isinstance(data.get(field),list): continue
        for i,item in enumerate(data[field]):
            if not isinstance(item,dict):
                errors.append(f"{field}[{i}] must be a mapping"); continue
            if not item.get("id"): errors.append(f"{field}[{i}].id is required")
            if field=="hypotheses":
                for f in ("statement","risk","test","success_metric"):
                    if not item.get(f): errors.append(f"{field}[{i}].{f} is required")
                if item.get("risk") not in {"low","medium","high"}: errors.append(f"{field}[{i}].risk must be low, medium, or high")
    ids={}
    for field in ("hypotheses","experiments","evidence","learnings","decisions"):
        for i,item in enumerate(data.get(field) or []):
            if isinstance(item,dict) and item.get("id"):
                if item["id"] in ids: errors.append(f"duplicate id {item['id']!r}")
                ids[item["id"]]=f"{field}[{i}]"
    hids={x.get("id") for x in (data.get("hypotheses") or []) if isinstance(x,dict)}
    for i,e in enumerate(data.get("experiments") or []):
        if isinstance(e,dict) and e.get("hypothesis_id") and e["hypothesis_id"] not in hids:
            errors.append(f"experiments[{i}].hypothesis_id references unknown hypothesis {e['hypothesis_id']!r}")
    sdd=data.get("sdd",{})
    if isinstance(sdd,dict):
        if sdd.get("provider") not in {"none","spec-kit"}: errors.append(f"invalid sdd.provider: {sdd.get('provider')!r}")
        if sdd.get("status") not in {"not_started","not_required","active","ready","blocked"}: errors.append(f"invalid sdd.status: {sdd.get('status')!r}")
    mvp=data.get("mvp",{})
    if isinstance(mvp,dict):
        if not isinstance(mvp.get("scope",[]),list): errors.append("mvp.scope must be a list")
        if not isinstance(mvp.get("out_of_scope",[]),list): errors.append("mvp.out_of_scope must be a list")
    if check_gate_requirements and isinstance(l,dict) and is_valid_gate(l.get("current_gate")) and l.get("current_gate")!="G0":
        errors.extend(f"current gate {l['current_gate']}: {e}" for e in gate_requirements_satisfied(data,l["current_gate"]))
    return errors
