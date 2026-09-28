import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("verifier",ROOT/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)
def test_oracle_replays_revocation_and_selects_robust_portfolio():
 exp=verifier.expected(ROOT/"data"); assert exp["selected_portfolio"]==["CHAIN-B","CHAIN-C"]; assert exp["robust_score"]==1.38; t1={r["chain_id"]:r for r in exp["replay"] if r["checkpoint"]=="T1"}; assert t1["CHAIN-A"]["blockers"]=="source_retracted"; assert t1["CHAIN-D"]["blockers"]=="sensitivity"
def test_reference_matches_oracle():
 exp=verifier.expected(ROOT/"data"); ref=json.loads((ROOT/"verifier_only/reference.json").read_text()); assert ref["selected_portfolio"]==exp["selected_portfolio"]
