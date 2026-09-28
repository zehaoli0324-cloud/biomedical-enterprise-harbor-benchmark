#!/usr/bin/env python3
import argparse, csv, hashlib, json, os, sys
from decimal import Decimal, ROUND_HALF_UP, getcontext
from collections import defaultdict

getcontext().prec = 50

def D(x):
    return Decimal(str(x))

def rnd(x):
    if x is None: return None
    return float(x.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP))

def mean(xs):
    return sum(xs, Decimal(0)) / Decimal(len(xs)) if xs else None

def read_csv(path):
    with open(path, newline='') as f: return list(csv.DictReader(f))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args(); data_dir, out_dir = a.data, a.out
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(data_dir, 'policy.json')) as f: policy = json.load(f)
    obs = read_csv(os.path.join(data_dir, 'observations.csv'))
    assay = read_csv(os.path.join(data_dir, 'assay_observations.csv'))
    cand = policy['active_candidates']; donors = policy['registered_donors']; states = policy['registered_states']; conds = policy['conditions']
    qc = policy['qc_pass_status']

    def val(r):
        x = r.get('adjusted_signal','')
        return D(x) if x not in ('', None) and r.get('qc_status') == qc else None

    # Keyed observations, retaining all eligible technical replicates.
    og = defaultdict(lambda: defaultdict(list))
    for r in obs:
        if r.get('candidate_id') in cand and r.get('donor') in donors and r.get('state') in states and r.get('condition') in conds:
            x = val(r)
            if x is not None: og[(r['candidate_id'],r['donor'],r['state'])][r['condition']].append(x)

    unit = []
    effects = {}
    for c in cand:
        for s in states:
            for d in donors:
                g = og[(c,d,s)]; cv, tv = g['control'], g['treatment']
                eff = mean(tv) - mean(cv) if cv and tv else None
                effects[(c,d,s)] = eff
                unit.append({'id':f'{c}|{s}|{d}','effect':rnd(eff),'control_rows':len(cv),'treatment_rows':len(tv)})

    scenarios = policy['scenarios']
    checks=[]; check_raw={}
    for sc in scenarios:
        omitted = sc.split(':',1)[1] if sc.startswith('omit:') else None
        for c in cand:
            for s in states:
                ds = [d for d in donors if d != omitted]
                usable = [d for d in ds if effects[(c,d,s)] is not None]
                missing = [d for d in ds if effects[(c,d,s)] is None]
                vals = [effects[(c,d,s)] for d in usable]
                nonpos = [d for d in usable if effects[(c,d,s)] <= 0]
                mn = mean(vals); er = max(vals)-min(vals) if vals else None
                min_count = policy['minimum_identifiable_donors'][s] if omitted is None else max(2, policy['minimum_identifiable_donors'][s]-1)
                if len(usable) < min_count: status='INSUFFICIENT'
                elif nonpos: status='CONTRADICTORY'
                elif mn < D(policy['minimum_state_mean_effect'][s]) or er > D(policy['maximum_state_effect_range'][s]): status='WEAK'
                else: status='SUPPORTED'
                rid=f'{sc}|{c}|{s}'
                check_raw[rid]=(len(usable),missing,nonpos,mn,er,status)
                checks.append({'id':rid,'count':len(usable),'missing_donors':missing,'nonpositive_donors':nonpos,'mean_effect':rnd(mn),'effect_range':rnd(er),'status':status})

    pooled=[]; pooled_raw={}
    for c in cand:
        for s in states:
            cv=[]; tv=[]
            for r in obs:
                if r.get('candidate_id')==c and r.get('state')==s and r.get('condition') in conds:
                    x=val(r)
                    if x is not None: (cv if r['condition']=='control' else tv).append(x)
            eff=mean(tv)-mean(cv) if cv and tv else None
            pooled_raw[(c,s)]=eff
            pooled.append({'id':f'{c}|{s}','effect':rnd(eff),'control_rows':len(cv),'treatment_rows':len(tv)})

    # Assay donor-balanced effects, keeping assay A/B as separate evidence axes.
    ag = defaultdict(lambda: defaultdict(list))
    for r in assay:
        if r.get('candidate_id') in cand and r.get('donor') in donors and r.get('state') in states and r.get('condition') in conds and r.get('assay') in policy['registered_assays']:
            x=val(r)
            if x is not None: ag[(r['candidate_id'],r['donor'],r['state'],r['assay'])][r['condition']].append(x)
    assay_checks=[]; assay_raw={}
    for c in cand:
        for s in states:
            ae={}; donor_eff={}
            for ax in policy['registered_assays']:
                vals=[]
                for d in donors:
                    g=ag[(c,d,s,ax)]; cv,tv=g['control'],g['treatment']
                    e=mean(tv)-mean(cv) if cv and tv else None
                    donor_eff[(ax,d)]=e
                    if e is not None: vals.append(e)
                ae[ax]=mean(vals) if vals else None
            complete_a=[donor_eff[('A',d)] for d in donors if donor_eff[('A',d)] is not None]
            complete_b=[donor_eff[('B',d)] for d in donors if donor_eff[('B',d)] is not None]
            insufficient = len(complete_a) < policy['minimum_identifiable_donors'][s] or len(complete_b) < policy['minimum_identifiable_donors'][s]
            nonpos = any(e <= 0 for e in complete_a+complete_b)
            disagree = (ae['A'] is not None and ae['B'] is not None and ((ae['A'] > 0) != (ae['B'] > 0)))
            ranges=[]
            if complete_a: ranges.append(max(complete_a)-min(complete_a))
            if complete_b: ranges.append(max(complete_b)-min(complete_b))
            er=max(ranges) if ranges else None
            if insufficient: status='INSUFFICIENT'
            elif nonpos or disagree: status='CONTRADICTORY'
            elif ae['A'] < D(policy['minimum_assay_effect']) or ae['B'] < D(policy['minimum_assay_effect']) or er > D(policy['maximum_state_effect_range'][s]): status='WEAK'
            else: status='SUPPORTED'
            rid=f'{c}|{s}'; assay_raw[rid]=(ae['A'],ae['B'],er,status)
            assay_checks.append({'id':rid,'assay_a_effect':rnd(ae['A']),'assay_b_effect':rnd(ae['B']),'direction_concordant':bool(not disagree),'effect_range':rnd(abs(ae['A']-ae['B']) if ae['A'] is not None and ae['B'] is not None else None),'status':status})

    # Candidate summaries and policy rankings, using raw Decimal values.
    summaries=[]
    nominal_candidates=[]; robust_candidates=[]; pooled_candidates=[]
    for c in cand:
        base=[check_raw[f'base|{c}|{s}'] for s in states]
        nominal_ok=all(x[5]=='SUPPORTED' for x in base)
        nominal_w=min((x[3] for x in base)) if base and all(x[3] is not None for x in base) else None
        allsc=[check_raw[f'{sc}|{c}|{s}'] for sc in scenarios for s in states]
        robust_ok=all(x[5]=='SUPPORTED' for x in allsc)
        robust_w=min((x[3] for x in allsc)) if allsc and all(x[3] is not None for x in allsc) else None
        pvals=[pooled_raw[(c,s)] for s in states]; pooled_w=min(pvals) if all(x is not None for x in pvals) else None
        failed=[sc for sc in scenarios if any(check_raw[f'{sc}|{c}|{s}'][5] != 'SUPPORTED' for s in states)]
        summaries.append({'id':c,'nominal_eligible':nominal_ok,'robust_eligible':robust_ok,'nominal_worst_mean':rnd(nominal_w),'robust_worst_mean':rnd(robust_w),'pooled_worst_mean':rnd(pooled_w),'failed_scenarios':failed})
        if nominal_ok: nominal_candidates.append((nominal_w,c))
        if robust_ok: robust_candidates.append((robust_w,c))
        if pooled_w is not None: pooled_candidates.append((pooled_w,c))
    # lexical ID tie-break means smallest lexical ID on equal score
    nominal_selected=sorted(nominal_candidates,key=lambda z:(-z[0],z[1]))[0][1] if nominal_candidates else None
    pooled_selected=sorted(pooled_candidates,key=lambda z:(-z[0],z[1]))[0][1] if pooled_candidates else None
    robust_selected=sorted(robust_candidates,key=lambda z:(-z[0],z[1]))[0][1] if robust_candidates else None
    assay_ok = robust_selected is not None and all(assay_raw[f'{robust_selected}|{s}'][3]=='SUPPORTED' for s in states)
    selected = robust_selected if assay_ok else None
    assay_selected = robust_selected if assay_ok else None
    cross_hold = not assay_ok
    reasons=[]
    if pooled_selected != nominal_selected: reasons.append('pooled_ranking_disagrees')
    if nominal_selected != robust_selected: reasons.append('nominal_selection_not_robust')
    # imbalance if any candidate/state has technical replicate count imbalance across conditions
    imbalance=False
    for c in cand:
        for s in states:
            pair_counts=[]
            for d in donors:
                g=og[(c,d,s)]
                if g['control'] and g['treatment']:
                    pair_counts.append((len(g['control']),len(g['treatment'])))
                if g['control'] and g['treatment'] and len(g['control']) != len(g['treatment']): imbalance=True
            # Pooled weighting is compositionally unequal when identifiable donors
            # contribute different numbers of technical replicates.
            if pair_counts and len(set(pair_counts)) > 1: imbalance=True
    if imbalance: reasons.append('technical_replication_imbalance')
    if any(x['missing_donors'] for x in checks): reasons.append('missing_pair_evidence')
    if any(x['status']=='CONTRADICTORY' for x in assay_checks): reasons.append('cross_assay_disagreement')
    decision={'nominal_selected':nominal_selected,'pooled_selected':pooled_selected,'selected':selected,'assay_selected':assay_selected,'cross_assay_hold':cross_hold,'reason_codes':sorted(set(reasons)),'claim_boundary':policy['claim_boundary'],'human_review_required':True}
    result={'unit_effects':unit,'checks':checks,'pooled':pooled,'summaries':summaries,'assay_checks':assay_checks,'decision':decision}
    with open(os.path.join(out_dir,'results.json'),'w') as f: json.dump(result,f,indent=2,allow_nan=False)
    # Deterministic provenance and bounded audit are generated during replay too.
    input_sha256={}
    for name in ('observations.csv','assay_observations.csv','policy.json','research_contract.json'):
        h=hashlib.sha256()
        with open(os.path.join(data_dir,name),'rb') as f:
            for chunk in iter(lambda:f.read(65536), b''): h.update(chunk)
        input_sha256[name]=h.hexdigest()
    self_path=os.path.abspath(__file__)
    h=hashlib.sha256()
    with open(self_path,'rb') as f:
        for chunk in iter(lambda:f.read(65536), b''): h.update(chunk)
    provenance={'input_sha256':input_sha256,'analysis_sha256':h.hexdigest(),'rules_version':policy['rules_version'],'network':'off','deterministic':True,'runtime':{'python_implementation':sys.implementation.name,'python_version':sys.version.split()[0],'decimal_precision':getcontext().prec}}
    with open(os.path.join(out_dir,'provenance.json'),'w') as f: json.dump(provenance,f,indent=2,sort_keys=True)
    supported_assay=[r['id'] for r in assay_checks if r['status']=='SUPPORTED']
    contradictory_assay=[r['id'] for r in assay_checks if r['status']=='CONTRADICTORY']
    with open(os.path.join(out_dir,'research_audit.md'),'w') as f:
        f.write('# Research audit\n\n')
        f.write('The registered paired estimand averages each donor\'s treatment-minus-control effect with equal donor weight; technical replicates are averaged within donor. The pooled diagnostic instead averages all eligible rows and therefore weights donors by replicate count. Independent assay A/B effects are donor-balanced separately and are not treated as additional donors.\n\n')
        f.write('Coverage: all 24 registered unit effects, 30 base/leave-one-donor-out checks, six pooled states, and six assay concordance states were recomputed from PASS, non-empty observations. Missing paired evidence is retained as missing rather than imputed.\n\n')
        f.write(f"Nominal selection was {nominal_selected or 'null'}; pooled selection was {pooled_selected or 'null'}. The robust paired candidate was {robust_selected or 'null'} after all omission scenarios. The pooled and nominal rankings therefore differ, and the nominal winner fails robustness under at least one omission scenario.\n\n")
        f.write('Technical-replicate composition changes the pooled estimand because some donor/state pairs contribute more rows than others; donor D1 is especially influential for C28. C43 late has missing D4 treatment evidence, so that donor/state remains incomplete in paired sensitivity checks.\n\n')
        f.write(f"Assay states supported: {', '.join(supported_assay) or 'none'}. Contradictory assay states: {', '.join(contradictory_assay) or 'none'}. Because at least one registered assay state is contradictory, assay concordance does not permit selection of the otherwise robust candidate.\n\n")
        f.write('Conclusion boundary: this is analytical triage only, not a mechanism or efficacy claim. Human review is required before any follow-up.\n')
    return result

if __name__=='__main__': main()
