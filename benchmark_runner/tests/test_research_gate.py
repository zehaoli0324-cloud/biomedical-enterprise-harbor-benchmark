import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/"scripts"))
    import calibrate_research_completion as calibration
    spec = importlib.util.spec_from_file_location("gated_adapter",ROOT/"benchmark_runner/adapters/codex_research_gate.py")
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    return calibration,adapter


def test_reference_controls_and_independent_variants(modules):
    calibration,_ = modules
    r = calibration.calibrate()
    assert r["status"] == "PASS"
    assert len(r["variants"]) == 5
    adversary = next(c for c in r["controls"] if c["id"] == "reproducible-wrong-answer")
    assert adversary["completion"] and not adversary["science"]


@pytest.mark.parametrize("initial_complete,max_attempts,expected_status,count",[
    (False,3,"accepted",2),(True,3,"accepted",1),(False,1,"attempt_budget_exhausted",1),
])
def test_real_return_loop(tmp_path,monkeypatch,modules,initial_complete,max_attempts,expected_status,count):
    import shutil
    calibration,adapter = modules
    workspace = tmp_path/"workspace"
    shutil.copytree(calibration.TASK/"data",workspace/"data")
    (workspace/"outputs").mkdir()
    prompt = tmp_path/"prompt.md"
    prompt.write_text("Complete the public research contract.")
    fake = tmp_path/"fake_agent.py"
    fake.write_text(
        "import json,pathlib,shutil,subprocess,sys\n"
        "i=int(sys.argv[1]);out=pathlib.Path(sys.argv[2]);data=pathlib.Path(sys.argv[3]);source=pathlib.Path(sys.argv[4])\n"
        "shutil.copy2(source,out/'analysis.py')\n"
        "subprocess.run([sys.executable,str(out/'analysis.py'),'--data',str(data),'--out',str(out)],check=True)\n"
        "if i==1:\n r=json.loads((out/'results.json').read_text());r['checks'].pop();(out/'results.json').write_text(json.dumps(r))\n"
    )
    calls = []
    def command(seconds):
        calls.append(seconds)
        return [sys.executable,str(fake),str(2 if initial_complete else len(calls)),str(workspace/"outputs"),str(workspace/"data"),str(ROOT/"scripts/audit_research_completion.py")]
    events = workspace/"events.jsonl"
    archive = tmp_path/"attempts"
    code = adapter.run_loop(command,workspace,prompt,events,archive,max_attempts,120)
    result = json.loads((archive/"result.json").read_text())
    assert result["status"] == expected_status
    assert len(result["attempts"]) == count
    assert code == (0 if expected_status == "accepted" else 2)
    if count == 2:
        feedback = (archive/"attempt-02/prompt.md").read_text()
        assert "record_coverage:checks" in feedback
        assert "C17" not in feedback and "0.39" not in feedback
        assert result["attempts"][0]["status"] == "returned"
        assert len(json.loads((archive/"attempt-01/submission/results.json").read_text())["checks"]) == 29
        assert len(json.loads((archive/"attempt-02/submission/results.json").read_text())["checks"]) == 30


def test_input_mutation_ends_without_feedback(tmp_path,modules):
    import shutil
    calibration,adapter = modules
    workspace = tmp_path/"workspace"
    shutil.copytree(calibration.TASK/"data",workspace/"data")
    (workspace/"outputs").mkdir()
    prompt = tmp_path/"prompt.md";prompt.write_text("task")
    fake = tmp_path/"mutate.py"
    fake.write_text("from pathlib import Path\nPath('data/policy.json').write_text('{}')\n")
    code = adapter.run_loop(lambda _: [sys.executable,str(fake)],workspace,prompt,workspace/"events.jsonl",tmp_path/"attempts",3,120)
    assert code == 2
    result = json.loads((tmp_path/"attempts/result.json").read_text())
    assert result["status"] == "input_integrity_error"
    assert len(result["attempts"]) == 1


def test_timeout_archives_completion_receipt_without_becoming_pass(tmp_path, modules):
    import shutil
    calibration, adapter = modules
    workspace = tmp_path / "workspace"
    shutil.copytree(calibration.TASK / "data", workspace / "data")
    (workspace / "outputs").mkdir()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("task")
    fake = tmp_path / "timeout_with_outputs.py"
    fake.write_text(
        "import pathlib,shutil,subprocess,sys\n"
        "out=pathlib.Path(sys.argv[1]);data=pathlib.Path(sys.argv[2]);source=pathlib.Path(sys.argv[3])\n"
        "shutil.copy2(source,out/'analysis.py')\n"
        "subprocess.run([sys.executable,str(out/'analysis.py'),'--data',str(data),'--out',str(out)],check=True)\n"
        "raise SystemExit(124)\n"
    )
    command = lambda _: [sys.executable, str(fake), str(workspace / "outputs"), str(workspace / "data"), str(ROOT / "scripts/audit_research_completion.py")]
    archive = tmp_path / "attempts"
    code = adapter.run_loop(command, workspace, prompt, workspace / "events.jsonl", archive, 3, 120)
    result = json.loads((archive / "result.json").read_text())
    assert code == 124
    assert result["status"] == "timeout_output_complete"
    assert result["attempts"][0]["completion"] == {"accepted": True, "issues": []}
    assert (archive / "attempt-01/completion_check/receipt.json").is_file()
