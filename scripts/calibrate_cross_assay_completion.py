import csv
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT/"benchmarks/eb006-research-completion-011"
sys.path.insert(0,str(ROOT))
from benchmark_runner.research_gate import check, digest, load, save
from audit_cross_assay_completion import solve


def verifier():
    spec = importlib.util.spec_from_file_location("research_verifier",TASK/"verifier.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference(out,data):
    out.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/"scripts/audit_cross_assay_completion.py",out/"analysis.py")
    subprocess.run([sys.executable,str(out/"analysis.py"),"--data",str(data),"--out",str(out)],check=True)


def calibrate():
    v = verifier()
    data = TASK/"data"
    expected = v.expected(data)
    assert not v.compare(solve(data),expected)
    assert expected["decision"]["selected"] is None
    controls,variants = [],[]
    with tempfile.TemporaryDirectory(prefix="research-controls-") as tmp:
        tmp = Path(tmp)
        out = tmp/"outputs"
        reference(out,data)
        gate = check(out,data,tmp/"positive-gate")
        assert gate["accepted"],gate
        ok,errors = v.verify(out,data)
        assert ok,errors
        controls.append({"id":"reference","completion":True,"science":True})
        for name,mutate in [
            ("missing-sensitivity",lambda r:r["checks"].pop()),
            ("missing-alternative",lambda r:r.pop("pooled")),
            ("duplicate-record",lambda r:r["checks"].append(r["checks"][0])),
        ]:
            reference(out,data)
            r = load(out/"results.json")
            mutate(r)
            save(out/"results.json",r)
            receipt = check(out,data,tmp/name)
            assert not receipt["accepted"]
            assert all("C17" not in issue and "C43" not in issue and "0.39" not in issue for issue in receipt["issues"])
            controls.append({"id":name,"completion":False,"issues":receipt["issues"]})
        reference(out,data)
        r = load(out/"results.json")
        r["decision"]["selected"] = r["decision"]["nominal_selected"]
        save(out/"results.json",r)
        # A deterministic constant program passes completion, but not science.
        (out/"analysis.py").write_text("import argparse,json,pathlib\np=argparse.ArgumentParser();p.add_argument('--data');p.add_argument('--out');a=p.parse_args();d=pathlib.Path(a.out);d.mkdir(parents=True,exist_ok=True);(d/'results.json').write_text("+repr(json.dumps(r))+")\n")
        prov = load(out/"provenance.json")
        prov["analysis_sha256"] = digest(out/"analysis.py")
        save(out/"provenance.json",prov)
        receipt = check(out,data,tmp/"constant-program")
        assert receipt["accepted"],receipt
        ok,errors = v.verify(out,data)
        assert not ok and any("perturbation" in error for error in errors)
        controls.append({"id":"reproducible-wrong-answer","completion":True,"science":False,"errors":errors})
        for name in ("row-order","replicate-balance","influence-repair","scope-noise","threshold-hold"):
            target = tmp/name
            shutil.copytree(data,target)
            with (target/"observations.csv").open(newline="") as handle:
                reader = csv.DictReader(handle)
                fields,rows = reader.fieldnames,list(reader)
            p = load(target/"policy.json")
            if name == "row-order":
                rows.reverse()
            if name == "replicate-balance":
                rows = [r for r in rows if r["technical_replicate"] == "1"]
            if name == "influence-repair":
                for row in rows:
                    if row["candidate_id"] == "C43" and row["state"] == "late" and row["condition"] == "treatment" and row["donor"] in ("D2","D3"):
                        row["adjusted_signal"] = "1.43" if row["donor"] == "D2" else "1.63"
            if name == "scope-noise":
                for row in rows:
                    if row["candidate_id"] == "C90":
                        row["adjusted_signal"] = "99999"
            if name == "threshold-hold":
                p["minimum_state_mean_effect"]["late"] = 0.8
                save(target/"policy.json",p)
            with (target/"observations.csv").open("w",newline="") as handle:
                writer = csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            truth = v.expected(target)
            assert not v.compare(solve(target),truth),name
            if name in ("row-order","scope-noise"):
                assert not v.compare(truth,expected)
            if name == "influence-repair":
                assert truth["decision"]["selected"] is None
            if name == "threshold-hold":
                assert truth["decision"]["selected"] is None
            variants.append({"id":name,"oracle_agreement":True,"decision":truth["decision"]})
    return {"status":"PASS","controls":controls,"variants":variants,"expected":expected}


def main():
    if (TASK/"quality/pretrial_freeze.json").exists():
        raise RuntimeError("Already frozen; use calibrate() for non-persisting checks")
    r = calibrate()
    save(TASK/"verifier_only/reference.json",r["expected"])
    save(TASK/"controls/calibration_results.json",{k:v for k,v in r.items() if k!="expected"})
    paths = [TASK/"verifier.py",TASK/"instruction.md",TASK/"task.yaml",*sorted((TASK/"data").glob("*"))]
    code = [ROOT/"benchmark_runner/research_gate.py",ROOT/"benchmark_runner/adapters/codex_research_gate.py",ROOT/"benchmark_runner/adapters/codex_complete_turn.py",ROOT/"benchmark_runner/adapters/codex_gpt55.py",ROOT/"scripts/audit_cross_assay_completion.py"]
    save(TASK/"quality/pretrial_freeze.json",{"sha256":{p.relative_to(TASK).as_posix():digest(p) for p in paths},"runtime_sha256":{p.relative_to(ROOT).as_posix():digest(p) for p in code}})
    save(TASK/"quality/readiness.json",{"status":"PRETRIAL_VALIDATED","target_model_trial":"NOT_RUN","human_review":"NOT_RUN","isolated_replay":"NOT_RUN","release_ready":False})
    print(json.dumps({"status":r["status"],"controls":len(r["controls"]),"variants":len(r["variants"]),"decision":r["expected"]["decision"]},indent=2))


if __name__ == "__main__":
    main()
