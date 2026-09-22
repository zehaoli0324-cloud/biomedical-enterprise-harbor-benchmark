import importlib.util, json
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("verifier",TASK/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)
def test_oracle_selects_adaptive_policy():
 exp=verifier.expected(TASK/"data"); assert exp["selected_stage1_request_id"]=="R-ADAPTIVE"; assert exp["selected_stage2_policy"]=={"signal_high":"R-SELECT","signal_low":"R-CORR"}; assert exp["worst_case_max_critical_residual"]==0.25
def test_reference_shape_is_deterministic():
 assert verifier.expected(TASK/"data")==verifier.expected(TASK/"data")
def test_fixed_stage2_policy_is_not_selected():
 exp=verifier.expected(TASK/"data"); assert not any(p["eligible"] and len(set(p["stage2_policy"].values()))==1 for p in exp["policies"] if p["stage1_request_id"]=="R-ADAPTIVE")
