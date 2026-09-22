import importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("verifier",ROOT/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)
def test_oracle_selects_provenance_safe_chain():
    exp=verifier.expected(ROOT/"data"); assert exp["selected_chain"]=="CHAIN-A"; assert exp["chains"]["CHAIN-B"]["blockers"]==["hash","upstream_hash"]; assert "inventory_or_quorum" in exp["chains"]["CHAIN-C"]["blockers"]; assert "claim_boundary" in exp["chains"]["CHAIN-D"]["blockers"]
def test_reference_matches_oracle():
    exp=verifier.expected(ROOT/"data"); ref=json.loads((ROOT/"verifier_only/reference.json").read_text()); assert ref["selected_chain"]==exp["selected_chain"]

def test_handoff_cross_artifact_mutation_fails(tmp_path):
    exp=verifier.expected(ROOT/"data"); case=json.loads((ROOT/"data/case.json").read_text())
    (tmp_path/"chain.json").write_text(json.dumps({"selected_chain":exp["selected_chain"],"rules_version":exp["rules_version"],"chains":exp["chains"]}))
    fields=["artifact_id","chain_id","stage","upstream_hash","content_hash","claim_permission","status"]
    with (tmp_path/"handoff.tsv").open("w") as handle:
        handle.write("\t".join(fields)+"\n")
        for artifact in case["artifacts"]:
            handle.write("\t".join([artifact["artifact_id"],"CHAIN-"+artifact["artifact_id"].split("-")[1],artifact["stage"],artifact.get("upstream_hash") or "",artifact["content_hash"],"operational",artifact["status"]])+"\n")
    (tmp_path/"audit.md").write_text("Claim permission, upstream hash, inventory, human review, stop conditions and not experimental proof are recorded.")
    (tmp_path/"manifest.json").write_text(json.dumps({"input_sha256":exp["hashes"],"rules_version":exp["rules_version"],"deterministic":True}))
    ok,errors=verifier.verify(tmp_path,ROOT/"data",ROOT/"verifier_only/reference.json")
    assert not ok and any("handoff claim_permission mismatch" in error for error in errors)

def test_equivalent_root_null_and_manifest_hash_aliases_pass(tmp_path):
    exp=verifier.expected(ROOT/"data"); case=json.loads((ROOT/"data/case.json").read_text())
    (tmp_path/"chain.json").write_text(json.dumps({"selected_chain":exp["selected_chain"],"rules_version":exp["rules_version"],"chains":[{"chain_id":key,**value} for key,value in exp["chains"].items()]}))
    fields=["artifact_id","chain_id","stage","upstream_hash","content_hash","claim_permission","status"]
    with (tmp_path/"handoff.tsv").open("w") as handle:
        handle.write("\t".join(fields)+"\n")
        for artifact in case["artifacts"]:
            upstream="null" if artifact.get("upstream_hash") is None else artifact["upstream_hash"]
            permission="descriptive" if artifact["artifact_id"].endswith("-D") else "associational"
            handle.write("\t".join([artifact["artifact_id"],"CHAIN-"+artifact["artifact_id"].split("-")[1],artifact["stage"],upstream,artifact["content_hash"],permission,artifact["status"]])+"\n")
    (tmp_path/"audit.md").write_text("Claim permission, upstream hash, inventory, human review, stop conditions and not experimental proof are recorded.")
    (tmp_path/"manifest.json").write_text(json.dumps({"case_sha256":exp["hashes"]["case.json"],"rules_sha256":exp["hashes"]["rules.json"],"rules_version":exp["rules_version"],"deterministic":True}))
    ok,errors=verifier.verify(tmp_path,ROOT/"data",ROOT/"verifier_only/reference.json")
    assert ok, errors
