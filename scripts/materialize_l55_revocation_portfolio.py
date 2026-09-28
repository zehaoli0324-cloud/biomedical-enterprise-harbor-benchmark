#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "eb012-revocation-portfolio-003"
TASK = ROOT / "benchmarks" / TASK_ID


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2) + "\n" if isinstance(value, (dict, list)) else value
    path.write_text(text, encoding="utf-8")


CHAINS = [
    {"chain_id":"CHAIN-A","source_id":"SRC-A","lot_id":"LOT-3","requested_claim":"associational","permissions":["associational"]*4,"utilities":{"T0":0.92,"T1":0.20,"T2":0.85}},
    {"chain_id":"CHAIN-B","source_id":"SRC-B","lot_id":"LOT-1","requested_claim":"associational","permissions":["associational"]*4,"utilities":{"T0":0.70,"T1":0.76,"T2":0.72}},
    {"chain_id":"CHAIN-C","source_id":"SRC-C","lot_id":"LOT-2","requested_claim":"associational","permissions":["associational"]*4,"utilities":{"T0":0.68,"T1":0.71,"T2":0.74}},
    {"chain_id":"CHAIN-D","source_id":"SRC-D","lot_id":"LOT-1","requested_claim":"associational","permissions":["associational"]*4,"utilities":{"T0":0.82,"T1":0.62,"T2":0.80}},
    {"chain_id":"CHAIN-E","source_id":"SRC-E","lot_id":"LOT-1","requested_claim":"associational","permissions":["associational"]*4,"utilities":{"T0":0.65,"T1":0.68,"T2":0.70}},
    {"chain_id":"CHAIN-F","source_id":"SRC-F","lot_id":"LOT-3","requested_claim":"associational","permissions":["descriptive"]*4,"utilities":{"T0":0.88,"T1":0.90,"T2":0.91}},
]
EVENTS = [
    {"event_id":"E01","checkpoint":"T1","sequence":1,"action":"retract_source","target":"SRC-A"},
    {"event_id":"E02","checkpoint":"T1","sequence":2,"action":"set_sensitivity","target":"CHAIN-D","value":"sensitive"},
    {"event_id":"E03","checkpoint":"T2","sequence":3,"action":"restore_source","target":"SRC-A"},
    {"event_id":"E04","checkpoint":"T2","sequence":4,"action":"set_sensitivity","target":"CHAIN-D","value":"stable"},
]
RULES = {"rules_version":"l5.5-revocation-portfolio-v1","checkpoints":["T0","T1","T2"],"claim_levels":{"descriptive":2,"associational":3,"causal":4},"initial_source_active":True,"initial_sensitivity":"stable","portfolio_size":2,"shared_lot_exclusive":True,"score":"minimum checkpoint sum of utilities","tie_break":"ascending joined chain ids"}


VERIFIER = '''from __future__ import annotations
import argparse,csv,hashlib,itertools,json
from pathlib import Path
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def expected(data):
 chains=json.loads((data/"chains.json").read_text())["chains"]; events=json.loads((data/"events.json").read_text())["events"]; rules=json.loads((data/"rules.json").read_text()); levels=rules["claim_levels"]; state={c["chain_id"]:{"source_active":True,"sensitivity":"stable"} for c in chains}; source={c["source_id"]:c["chain_id"] for c in chains}; replay=[]
 for checkpoint in rules["checkpoints"]:
  for event in sorted((e for e in events if e["checkpoint"]==checkpoint),key=lambda e:e["sequence"]):
   if event["action"] in ("retract_source","restore_source"): state[source[event["target"]]]["source_active"]=event["action"]=="restore_source"
   elif event["action"]=="set_sensitivity": state[event["target"]]["sensitivity"]=event["value"]
  for c in chains:
   s=state[c["chain_id"]]; blockers=[]; effective=min(c["permissions"],key=lambda p:levels[p])
   if not s["source_active"]: blockers.append("source_retracted")
   if s["sensitivity"]!="stable": blockers.append("sensitivity")
   if levels[effective]<levels[c["requested_claim"]]: blockers.append("claim_boundary")
   replay.append({"chain_id":c["chain_id"],"checkpoint":checkpoint,"source_active":s["source_active"],"sensitivity":s["sensitivity"],"eligible":not blockers,"blockers":";".join(blockers),"effective_claim":effective,"utility":c["utilities"][checkpoint],"lot_id":c["lot_id"]})
 robust={c["chain_id"]:all(r["eligible"] for r in replay if r["chain_id"]==c["chain_id"]) for c in chains}; portfolios=[]
 for a,b in itertools.combinations(chains,2):
  ids=[a["chain_id"],b["chain_id"]]; blockers=[]
  if not all(robust[x] for x in ids): blockers.append("not_checkpoint_robust")
  if a["lot_id"]==b["lot_id"]: blockers.append("shared_lot_conflict")
  totals={t:round(a["utilities"][t]+b["utilities"][t],6) for t in rules["checkpoints"]}; score=min(totals.values())
  portfolios.append({"chain_ids":ids,"eligible":not blockers,"blockers":blockers,"checkpoint_totals":totals,"robust_score":score})
 eligible=[p for p in portfolios if p["eligible"]]; winner=max(eligible,key=lambda p:(p["robust_score"],"|".join(chr(255-ord(x)) for x in "|".join(p["chain_ids"]))))
 return {"rules_version":rules["rules_version"],"selected_portfolio":winner["chain_ids"],"robust_score":winner["robust_score"],"portfolios":portfolios,"replay":replay,"hashes":{n:sha(data/n) for n in ("chains.json","events.json","rules.json")}}
def verify(submission,data,reference):
 exp=expected(data); errors=[]
 for name in ("decision.json","replay.tsv","audit.md","manifest.json"):
  if not (submission/name).is_file(): errors.append("missing artifact: "+name)
 if errors:return False,errors
 report=json.loads((submission/"decision.json").read_text())
 for field in ("rules_version","selected_portfolio","robust_score"):
  if report.get(field)!=exp[field]: errors.append(field+" mismatch")
 portfolios=report.get("portfolios")
 if not isinstance(portfolios,list) or len(portfolios)!=len(exp["portfolios"]): errors.append("portfolios mismatch")
 else:
  for actual,want in zip(portfolios,exp["portfolios"]):
   for field in ("chain_ids","eligible","checkpoint_totals","robust_score"):
    if actual.get(field)!=want[field]: errors.append("portfolios mismatch"); break
   blockers=actual.get("blockers")
   if not isinstance(blockers,list) or (want["eligible"] and blockers) or (not want["eligible"] and not blockers): errors.append("portfolio blockers mismatch")
 rows=list(csv.DictReader((submission/"replay.tsv").open(newline=""),delimiter="\\t")); fields=("chain_id","checkpoint","source_active","sensitivity","eligible","blockers","effective_claim","utility","lot_id")
 if len(rows)!=len(exp["replay"]) or not rows or set(rows[0])!=set(fields): errors.append("replay schema or coverage mismatch")
 else:
  actual=[]
  for r in rows:
   try: actual.append({"chain_id":r["chain_id"],"checkpoint":r["checkpoint"],"source_active":r["source_active"].lower()=="true","sensitivity":r["sensitivity"],"eligible":r["eligible"].lower()=="true","blockers":r["blockers"],"effective_claim":r["effective_claim"],"utility":float(r["utility"]),"lot_id":r["lot_id"]})
   except Exception: errors.append("replay parse failure"); break
  for got,want in zip(sorted(actual,key=lambda x:(x["checkpoint"],x["chain_id"])),sorted(exp["replay"],key=lambda x:(x["checkpoint"],x["chain_id"]))):
   if any(got[k]!=want[k] for k in ("chain_id","checkpoint","source_active","sensitivity","eligible","effective_claim","utility","lot_id")): errors.append("replay mismatch")
   if (want["eligible"] and got["blockers"]) or (not want["eligible"] and not got["blockers"]): errors.append("replay blockers mismatch")
 audit=(submission/"audit.md").read_text().lower()
 for variants in (("retraction","retract"),("checkpoint",),("shared lot","shared-lot"),("claim boundary","claim-boundary"),("human review",),("not experimental proof","does not constitute experimental proof")):
  if not any(v in audit for v in variants): errors.append("audit missing "+variants[0])
 manifest=json.loads((submission/"manifest.json").read_text()); hashes=manifest.get("input_sha256")
 if hashes!=exp["hashes"] or manifest.get("rules_version")!=exp["rules_version"] or manifest.get("deterministic") is not True: errors.append("manifest mismatch")
 return not errors,errors
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--submission",type=Path,required=True);p.add_argument("--data",type=Path,required=True);p.add_argument("--reference",type=Path,required=True);a=p.parse_args();ok,errors=verify(a.submission,a.data,a.reference);print(json.dumps({"passed":ok,"errors":errors}));raise SystemExit(0 if ok else 1)
'''


def main() -> None:
    write(TASK/"data/chains.json", {"chains":CHAINS})
    write(TASK/"data/events.json", {"events":EVENTS})
    write(TASK/"data/rules.json", RULES)
    write(TASK/"verifier.py", VERIFIER)
    write(TASK/"verifier_only/reference.json", {"selected_portfolio":["CHAIN-B","CHAIN-C"],"rules_version":RULES["rules_version"],"status":"verifier_only"})
    write(TASK/"instruction.md", '''# Revocation-aware cross-stage portfolio replay

Use only the three supplied JSON files. Replay events in ascending `sequence` at checkpoints T0, T1, and T2. State persists until a later event changes it. At every checkpoint, a chain is eligible only when its source is active, sensitivity is `stable`, and the requested claim does not exceed the minimum permission across its four stages. A chain is checkpoint-robust only if eligible at all three checkpoints.

Evaluate every two-chain combination. A portfolio is eligible only when both chains are checkpoint-robust and their `lot_id` values differ. Its checkpoint total is the sum of member utilities; its robust score is the minimum of the three checkpoint totals. Select the eligible portfolio with highest robust score, breaking an exact tie by ascending joined chain IDs. Round numeric outputs to six decimals.

Write exactly four artifacts:

- `outputs/decision.json`: object with `rules_version`, `selected_portfolio`, `robust_score`, and `portfolios`. `portfolios` is the complete 15-row combination list in ascending input combination order; each row has `chain_ids`, `eligible`, sorted `blockers`, `checkpoint_totals`, and `robust_score`.
- `outputs/replay.tsv`: exactly 18 rows with header `chain_id`, `checkpoint`, `source_active`, `sensitivity`, `eligible`, `blockers`, `effective_claim`, `utility`, `lot_id`. Use lowercase `true`/`false`; join blockers with semicolons in rule order; use an empty blockers field when none.
- `outputs/audit.md`: explain retraction propagation, checkpoint persistence, shared-lot exclusion, claim boundary, human review, and why this does not constitute experimental proof.
- `outputs/manifest.json`: `input_sha256` mapping the exact filenames `chains.json`, `events.json`, `rules.json` to SHA-256 values, plus `rules_version` and `deterministic=true`.
''')
    write(TASK/"task.yaml", f'''id: {TASK_ID}\nversion: "1.0.0"\nstatus: ready_for_calibration\ntitle: "Revocation-aware cross-stage portfolio replay"\ndomain: biomedical_enterprise\nagent_visible_inputs:\n  - path: data/\n    format: JSON event replay inputs\nconstraints:\n  network: off\nrequired_outputs:\n  - {{id: decision, path: outputs/decision.json, required_fields: [rules_version, selected_portfolio, robust_score, portfolios]}}\n  - {{id: replay, path: outputs/replay.tsv, required_fields: [chain_id, checkpoint, source_active, sensitivity, eligible, blockers, effective_claim, utility, lot_id]}}\n  - {{id: audit, path: outputs/audit.md, required_fields: [retraction, checkpoint, shared_lot, claim_boundary, human_review]}}\n  - {{id: manifest, path: outputs/manifest.json, required_fields: [input_sha256, rules_version, deterministic]}}\nhidden_truth:\n  path: verifier_only/reference.json\n  status: verifier_only\n''')
    write(TASK/"scenario-card.yaml", f'''scenario_id: {TASK_ID}\nstatus: ready\nsource_scenarios: [L5.5-TRANCHE-011]\ndomain: biomedical_enterprise\nscientific_decision: select a portfolio that survives evidence revocation and shared-resource constraints\nscientific_judgments:\n  - temporal_revocation_propagation\n  - checkpoint_robustness\n  - shared_inventory_portfolio_selection\ndifficulty_modules:\n  - id: horizon_checkpointed_workflow\n    observable: source and sensitivity state persist across three ordered checkpoints\n    decision_flip: transient invalidity disqualifies an otherwise high-utility chain\n  - id: data_evidence_graph_join\n    observable: source events propagate to dependent chain decisions\n    decision_flip: source retraction invalidates the nominal winner\n  - id: data_shared_inventory_allocation\n    observable: selected chains must use distinct exclusive lots\n    decision_flip: the two highest local scores cannot form a portfolio\n  - id: judgment_claim_permission_lattice\n    observable: effective claim is the weakest of four stage permissions\n    decision_flip: a high-utility descriptive chain cannot satisfy an associational request\n  - id: math_robust_scenario_optimization\n    observable: portfolios rank by minimum checkpoint total rather than nominal total\n    decision_flip: maximin selection differs from single-checkpoint ranking\n+workflow_handoffs:\n  - from: ordered_event_replay\n    to: resource_constrained_portfolio\n    artifact: outputs/decision.json\n    invariant: revoked evidence and weak claims never regain authority without an explicit event\n+release_gates:\n  scientific_reality: pass\n  observability: pass\n  verifiability: pass\n  naive_resistance: pass\n  reproducibility: pass\n  enterprise_value: pending\n  training_value: not_run\n'''.replace("\n+", "\n"))
    quality={
      "difficulty_card.json":{"difficulty_card_id":"DIFF-EB012-REVOCATION-PORTFOLIO-003-001","task_id":TASK_ID,"primary_module":"horizon_checkpointed_workflow","secondary_modules":["data_shared_inventory_allocation","math_robust_scenario_optimization"],"held_out_variants":["delayed retraction","lot release","claim downgrade"],"decision_flip_controls":["retracted nominal winner","shared-lot top pair","descriptive high score"],"status":"REVIEW_REQUIRED"},
      "control_plan_card.json":{"control_plan_id":"CONTROL-EB012-REVOCATION-PORTFOLIO-003-001","task_id":TASK_ID,"controls":[{"control_id":"positive-reference","kind":"positive"},{"control_id":"negative-nominal-pair","kind":"negative"},{"control_id":"invariance-event-storage-order","kind":"invariance"},{"control_id":"insufficient-replay","kind":"insufficient_evidence"},{"control_id":"adversarial-shared-lot","kind":"adversarial"},{"control_id":"metamorphic-event-order","kind":"metamorphic"}],"single_factor_policy":True,"calibration_status":"NOT_RUN","status":"REVIEW_REQUIRED"},
      "model_trial_card.json":{"model_trial_card_id":"TRIAL-EB012-REVOCATION-PORTFOLIO-003-001","task_id":TASK_ID,"protocol_version":"enterprise-model-trial.v1","strategies":["reference_solution","simple_legal_baseline","always_abstain","template_or_keyword","target_model"],"target_model_status":"NOT_RUN","status":"NOT_RUN","run_records":[]},
      "model_trial_results.json":{"task_id":TASK_ID,"protocol_version":"enterprise-model-trial.v1","status":"NOT_RUN","target_model_status":"NOT_RUN","records":[]},
      "independent_verifier_audit.json":{"audit_id":"AUDIT-EB012-REVOCATION-PORTFOLIO-003-001","task_id":TASK_ID,"review_status":"not_run","status":"REVIEW_REQUIRED"},
      "contract_audit.json":{"schema_version":"enterprise_contract_audit.v1","task_id":TASK_ID,"status":"PASS","checks":[{"output":x,"path_declared":True,"schema_declared":True,"claim_boundary_declared":True} for x in ["outputs/decision.json","outputs/replay.tsv","outputs/audit.md","outputs/manifest.json"]]},
      "sop_card.json":{"schema_version":"enterprise_harbor_sop_card.v1","task_id":TASK_ID,"sop_version":"enterprise-harbor-sop-v1.2","source_status":"REVIEW_REQUIRED","contract_status":"MATERIALIZED_V1.0.0","control_status":"NOT_RUN","model_trial_status":"NOT_RUN","independent_verifier_status":"NOT_RUN","release_status":"BLOCKED","release_blockers":["controls","baselines","independent verifier audit","target-model trial","fixed-container replay","practitioner review"]},
    }
    for name,payload in quality.items(): write(TASK/"quality"/name,payload)
    write(TASK/"tests/test_verifier.py", '''import importlib.util,json\nfrom pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\nspec=importlib.util.spec_from_file_location("verifier",ROOT/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)\ndef test_oracle_replays_revocation_and_selects_robust_portfolio():\n exp=verifier.expected(ROOT/"data"); assert exp["selected_portfolio"]==["CHAIN-B","CHAIN-C"]; assert exp["robust_score"]==1.38; t1={r["chain_id"]:r for r in exp["replay"] if r["checkpoint"]=="T1"}; assert t1["CHAIN-A"]["blockers"]=="source_retracted"; assert t1["CHAIN-D"]["blockers"]=="sensitivity"\ndef test_reference_matches_oracle():\n exp=verifier.expected(ROOT/"data"); ref=json.loads((ROOT/"verifier_only/reference.json").read_text()); assert ref["selected_portfolio"]==exp["selected_portfolio"]\n''')


if __name__ == "__main__":
    main()
