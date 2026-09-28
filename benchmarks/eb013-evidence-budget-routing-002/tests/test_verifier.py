import importlib.util, json, runpy
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("verifier",TASK/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)
def test_oracle_selects_adaptive_policy():
 exp=verifier.expected(TASK/"data"); assert exp["selected_stage1_request_id"]=="R-ADAPTIVE"; assert exp["selected_stage2_policy"]=={"signal_high":"R-SELECT","signal_low":"R-CORR","signal_mid":"R-BALANCE"}; assert exp["worst_case_max_critical_residual"]==0.25
def test_reference_shape_is_deterministic():
 assert verifier.expected(TASK/"data")==verifier.expected(TASK/"data")
def test_fixed_stage2_policy_is_not_selected():
 exp=verifier.expected(TASK/"data"); assert not any(p["eligible"] and len(set(p["stage2_policy"].values()))==1 for p in exp["policies"] if p["stage1_request_id"]=="R-ADAPTIVE")
def test_adaptive_policy_covers_three_observation_states():
 exp=verifier.expected(TASK/"data"); assert set(exp["selected_stage2_policy"])=={"signal_high","signal_low","signal_mid"}

def test_incomplete_policy_is_audited_without_becoming_eligible():
 exp=verifier.expected(TASK/"data")
 fixed=next(policy for policy in exp["policies"] if policy["stage1_request_id"]=="R-FIXED")
 assert fixed["complete"] is False
 assert fixed["eligible"] is False
 assert fixed["stage2_policy"]=={"chem_clean":None,"chem_risk":None}

def test_summary_policy_rows_replay_without_weakening_route_checks(tmp_path):
 calibration=runpy.run_path(str(TASK.parent.parent/"scripts/run_l61_two_stage_calibration.py"))
 exp=calibration["reference"](tmp_path)
 decision=json.loads((tmp_path/"decision.json").read_text())
 decision["policies"]=[]
 for policy in exp["policies"]:
  row={key:policy[key] for key in ("stage1_request_id","stage2_policy","eligible","worst_case_max_critical_residual","worst_case_cost")}
  row["observation_states"]=list(policy["stage2_policy"])
  if not policy["complete"]:
   row["worst_case_max_critical_residual"]=0.5
  decision["policies"].append(row)
 (tmp_path/"decision.json").write_text(json.dumps(decision))
 passed,errors=verifier.verify(tmp_path,TASK/"data",TASK/"verifier_only/reference.json")
 assert passed,errors

def test_malformed_summary_returns_structured_failure(tmp_path):
 passed,errors=verifier.verify(tmp_path,TASK/"data",TASK/"verifier_only/reference.json")
 assert not passed
 assert errors and errors[0].startswith("missing artifact:")

def test_malformed_json_returns_structured_failure(tmp_path):
 for name in ("plan.json", "decision.json", "provenance.json", "route.tsv", "audit.md"):
  path=tmp_path/name
  path.write_text("{" if name.endswith(".json") else "", encoding="utf-8")
 passed,errors=verifier.verify(tmp_path,TASK/"data",TASK/"verifier_only/reference.json")
 assert not passed
 assert errors == ["invalid JSON: plan.json (JSONDecodeError)", "invalid JSON: decision.json (JSONDecodeError)", "invalid JSON: provenance.json (JSONDecodeError)"]

def test_reference_route_covers_each_observation_state(tmp_path):
 calibration=runpy.run_path(str(TASK.parent.parent/"scripts/run_l61_two_stage_calibration.py"))
 calibration["reference"](tmp_path)
 passed,errors=verifier.verify(tmp_path,TASK/"data",TASK/"verifier_only/reference.json")
 assert passed,errors

def test_route_missing_observation_state_fails(tmp_path):
 calibration=runpy.run_path(str(TASK.parent.parent/"scripts/run_l61_two_stage_calibration.py"))
 calibration["reference"](tmp_path)
 lines=(tmp_path/"route.tsv").read_text().splitlines()
 (tmp_path/"route.tsv").write_text("\n".join(lines[:-1])+"\n")
 passed,errors=verifier.verify(tmp_path,TASK/"data",TASK/"verifier_only/reference.json")
 assert not passed
 assert "route coverage mismatch" in errors
