from __future__ import annotations
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
 rows=list(csv.DictReader((submission/"replay.tsv").open(newline=""),delimiter="\t")); fields=("chain_id","checkpoint","source_active","sensitivity","eligible","blockers","effective_claim","utility","lot_id")
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
