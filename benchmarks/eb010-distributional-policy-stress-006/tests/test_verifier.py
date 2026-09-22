import csv, importlib.util, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("verifier",ROOT/"verifier.py"); verifier=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(verifier)

def test_oracle_is_distributionally_robust():
    exp=verifier.expected(ROOT/"data")
    assert exp["selected_policy"]=="P-ADAPT"
    assert exp["profile_winners"]["nominal"]=="P-NOMINAL"
    assert set(exp["leave_one_profile_out_winners"].values())=={"P-ADAPT"}
    assert exp["policies"]["P-OVERRUN"]["blockers"]==["budget"]
    assert exp["policies"]["P-INCOMPLETE"]["blockers"]==["branch_completeness"]

def test_reference_declares_current_oracle():
    exp=verifier.expected(ROOT/"data"); ref=json.loads((ROOT/"verifier_only/reference.json").read_text())
    assert ref["selected_policy"]==exp["selected_policy"]

def test_equivalent_numeric_and_branch_representations_are_accepted(tmp_path):
    helpers=runpy.run_path(str(ROOT.parents[1]/"scripts/run_l53_distributional_stress_calibration.py"))
    out=tmp_path/"outputs"; helpers["write_reference"](verifier,out,ROOT/"data")
    report=json.loads((out/"policy.json").read_text())
    for policy in report["policies"].values(): policy["branches"]=list(policy["branches"].values())
    report["profile_best_expected"]["nominal"] += 1e-6
    (out/"policy.json").write_text(json.dumps(report))
    rows=list(csv.DictReader((out/"branches.tsv").open(newline=""),delimiter="\t"))
    with (out/"branches.tsv").open("w",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]),delimiter="\t"); writer.writeheader()
        for row in rows:
            for field in ("total_cost","utility"):
                if row[field]: row[field]=str(float(row[field]))
            writer.writerow(row)
    (out/"audit.md").write_text((out/"audit.md").read_text().replace("Future outcome","Future-outcome"))
    passed,errors=verifier.verify(out,ROOT/"data",ROOT/"verifier_only/reference.json")
    assert passed,errors
