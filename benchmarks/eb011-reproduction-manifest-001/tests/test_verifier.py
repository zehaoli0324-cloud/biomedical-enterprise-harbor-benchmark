import importlib.util
from pathlib import Path
TASK=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("verifier",TASK/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)
def test_oracle_selects_declared_adaptive_policy():
 exp=verifier.expected(TASK/"data"); assert exp["selected_stage1_request_id"]=='D-MANIFEST'; assert exp["selected_stage2_policy"]=={'topology_mismatch': 'D-REBUILD', 'parameter_drift': 'D-PIN'}
def test_oracle_is_deterministic():
 assert verifier.expected(TASK/"data")==verifier.expected(TASK/"data")
def test_winner_is_not_a_fixed_stage2_shortcut():
 exp=verifier.expected(TASK/"data"); assert len(set(exp["selected_stage2_policy"].values()))>1
