"""Freeze development selection, then run a fresh recovery study."""
from __future__ import annotations
import csv, hashlib, json, platform, time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import mean
import numpy as np
from metarouter.recovery_study import Dataset,REGIMES,BASE_POLICIES,POLICIES,RISK,THRESHOLDS,ENGINES,episode,Environment,close
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/meta-routing/intellisys2027'
PAPER=ROOT/'papers/meta-routing/intellisys2027'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvwrite(path,rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'traces.jsonl').exists(),'Existing evaluated run must not be silently overwritten.'
    datasets={n:Dataset(n,ROOT/f'benchmarks/recovery2027/raw/{n}.zip') for n in ('iris','wine','banknote')}
    queries={s:[q for n,d in datasets.items() for q in d.queries(n,s)] for s in ('dev','test')}
    csvwrite(OUT/'queries.csv',[asdict(q) for s in queries.values() for q in s])
    # Audit actual engines against Decimal before any faulted comparison.
    for qs in queries.values():
        for q in qs:
            for e in ENGINES:assert close(datasets[q.dataset].execute(q,e),datasets[q.dataset].reference(q))
    risk={}
    for op in RISK:
        outcomes=[]
        for q in queries['dev']:
            if q.operation!=op:continue
            for regime in REGIMES[:4]:
                for seed in range(10):
                    env=Environment(datasets[q.dataset],q,regime,seed,1)
                    r=env.call('sqlite')
                    if r.status=='ok':outcomes.append(not close(r.value,datasets[q.dataset].reference(q)))
        risk[op]=mean(outcomes)
    dev=[];selection={};thresholds={}
    for budget in (1,2,3):
        scores=defaultdict(list)
        for q in queries['dev']:
            for regime in REGIMES[:4]:
                for seed in range(10):
                    for policy in BASE_POLICIES:
                        r=episode(datasets[q.dataset],q,regime,seed,budget,policy)
                        scores[policy].append(r['utility'])
                    for threshold in THRESHOLDS:
                        r=episode(datasets[q.dataset],q,regime,seed,budget,'risk_gate',risk,threshold)
                        scores[f'gate_{threshold}'].append(r['utility'])
        # Fixed-policy tie break follows declared policy order; gate tie break
        # prefers a higher threshold, reducing verification when utility ties.
        selection[budget]=max(BASE_POLICIES,key=lambda p:mean(scores[p]))
        thresholds[budget]=max(THRESHOLDS,key=lambda t:(mean(scores[f'gate_{t}']),t))
        dev.extend({'budget':budget,'policy':p,'mean_utility':mean(v)} for p,v in scores.items())
    csvwrite(OUT/'development_selection.csv',dev)
    config={'risk':risk,'gate_threshold':thresholds,'selected_fixed_policy':selection,
            'selection_data':'72 development queries; first four regimes only; ten seeds',
            'utility':'correct - 4*wrong - 0.05*calls',
            'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'src/metarouter/recovery_study.py',Path(__file__),PAPER/'STUDY_PROTOCOL.md']},
            'raw_sha256':{n:digest(ROOT/f'benchmarks/recovery2027/raw/{n}.zip') for n in datasets},
            'queries_sha256':digest(OUT/'queries.csv'),'test_policy_tuning':False,
            'timestamp_before_test_unix':time.time(),'external_preregistration':False,
            'python':platform.python_version(),'numpy':np.__version__}
    (OUT/'frozen_config.json').write_text(json.dumps(config,indent=2)+'\n')
    # No test result has been evaluated when the fit/protocol record is written.
    print('Development frozen:',json.dumps({'risk':risk,'thresholds':thresholds,'fixed':selection}),flush=True)
    allrows=[]
    with (OUT/'traces.jsonl').open('w') as f:
        for regime in REGIMES:
            for q in queries['test']:
                for seed in range(10):
                    for budget in (1,2,3):
                        for policy in POLICIES:
                            actual=selection[budget] if policy=='dev_fixed' else policy
                            r=episode(datasets[q.dataset],q,regime,seed,budget,actual,risk,thresholds[budget])
                            r['executed_policy']=actual;r['policy']=policy
                            assert r['calls']<=budget and r['correct']+r['wrong']+r['abstain']==1
                            f.write(json.dumps(r)+'\n')
                            allrows.append({k:v for k,v in r.items() if k!='steps'})
            print('Evaluated',regime,flush=True)
    metrics=('correct','wrong','abstain','calls','utility','execution_ms')
    def aggregate(keys):
        groups=defaultdict(list)
        for r in allrows:groups[tuple(r[k] for k in keys)].append(r)
        out=[]
        for key,rs in sorted(groups.items()):
            row=dict(zip(keys,key));row['n_episodes']=len(rs)
            row.update({m:mean(r[m] for r in rs) for m in metrics})
            row['answered']=1-row['abstain'];row['wrong_given_answered']=row['wrong']/row['answered'] if row['answered'] else 0
            row['budget_compliance']=mean(r['calls']<=r['budget'] for r in rs)
            out.append(row)
        return out
    csvwrite(OUT/'summary.csv',aggregate(['regime','budget','policy']))
    csvwrite(OUT/'by_dataset.csv',aggregate(['dataset','regime','budget','policy']))
    csvwrite(OUT/'by_family.csv',aggregate(['operation','regime','budget','policy']))
    csvwrite(OUT/'by_query.csv',aggregate(['query_id','dataset','regime','budget','policy']))
    # Paired resampling of queries, averaging repeated fault seeds first.
    by=defaultdict(list)
    for r in allrows:by[r['query_id'],r['regime'],r['budget'],r['policy']].append(r)
    rng=np.random.default_rng(20271029);comparisons=[]
    for regime in REGIMES:
        for budget in (1,2,3):
            for baseline in ('dev_fixed','agreement','majority','sql_only'):
                arrays={m:[] for m in metrics[:5]}
                for name in datasets:
                    qs=[q for q in queries['test'] if q.dataset==name]
                    sampled=rng.integers(0,len(qs),size=(1000,len(qs)))
                    for metric in arrays:
                        delta=np.array([mean(r[metric] for r in by[q.query_id,regime,budget,'risk_gate'])-mean(r[metric] for r in by[q.query_id,regime,budget,baseline]) for q in qs])
                        arrays[metric].append((delta.mean(),delta[sampled].mean(axis=1)))
                for metric,parts in arrays.items():
                    boot=np.mean([p[1] for p in parts],axis=0)
                    comparisons.append({'regime':regime,'budget':budget,'treatment':'risk_gate','baseline':baseline,'metric':metric,'difference':mean(p[0] for p in parts),'ci_low':float(np.quantile(boot,.025)),'ci_high':float(np.quantile(boot,.975)),'query_clusters':72})
    csvwrite(OUT/'paired_comparisons.csv',comparisons)
    manifest={'episodes':len(allrows),'test_queries':72,'dev_queries':72,'seeds':10,'regimes':6,
              'policies':len(POLICIES),'budgets':[1,2,3],'dataset_rows':{n:len(d.rows) for n,d in datasets.items()},
              'frozen_config_sha256':digest(OUT/'frozen_config.json'),'traces_sha256':digest(OUT/'traces.jsonl'),
              'scope':'Actual numerical engines; authored query tasks; injected stress faults; no LLMs or production-rate claim.'}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Complete:',json.dumps(manifest),flush=True)
if __name__=='__main__':main()
