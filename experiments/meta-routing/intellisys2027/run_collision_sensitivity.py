"""Post-run sensitivity: independent fault events can yield identical wrong values.

Added after the main run exposed a structural zero-error property of
engine-specific offsets. Original frozen policies and fits remain unchanged.
"""
import csv,json,time,hashlib
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from unittest.mock import patch
from metarouter import recovery_study as study
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'results/meta-routing/intellisys2027'
Original=study.Environment
class CollidingEnvironment(Original):
    def call(self,engine):
        response=super().call(engine)
        if self.steps[-1]['injected_fault']=='independent_offset':
            value=response.value-(5.,7.,11.)[study.ENGINES.index(engine)]+7.
            response=study.Response(engine,'ok',value)
            self.steps[-1].update(value=value,injected_fault='independent_collision_offset')
        return response

def main():
    assert not (OUT/'collision_traces.jsonl').exists()
    config=json.loads((OUT/'frozen_config.json').read_text())
    (OUT/'collision_addendum.json').write_text(json.dumps({'status':'Post-main-run exploratory sensitivity; no retuning','reason':'Engine-specific offsets make agreement between wrong independent responses impossible; permit coinciding wrong values instead.','frozen_config_sha256':hashlib.sha256((OUT/'frozen_config.json').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'timestamp_before_extension':time.time()},indent=2)+'\n')
    groups=defaultdict(list)
    with patch.object(study,'Environment',CollidingEnvironment), (OUT/'collision_traces.jsonl').open('w') as f:
        for name in ('iris','wine','banknote'):
            data=study.Dataset(name,ROOT/f'benchmarks/recovery2027/raw/{name}.zip')
            for q in data.queries(name,'test'):
                for regime in ('independent','shifted'):
                    for seed in range(10):
                        for budget in (1,2,3):
                            for policy in study.POLICIES:
                                actual=config['selected_fixed_policy'][str(budget)] if policy=='dev_fixed' else policy
                                r=study.episode(data,q,regime,seed,budget,actual,config['risk'],config['gate_threshold'][str(budget)])
                                r['policy']=policy;r['regime']=regime+'_collision'
                                assert r['calls']<=budget
                                f.write(json.dumps(r)+'\n');groups[r['regime'],budget,policy].append(r)
    rows=[]
    for (regime,budget,policy),rs in sorted(groups.items()):
        row={'regime':regime,'budget':budget,'policy':policy,'n_episodes':len(rs)}
        row.update({m:mean(r[m] for r in rs) for m in ('correct','wrong','abstain','calls','utility','execution_ms')})
        row['answered']=1-row['abstain'];row['wrong_given_answered']=row['wrong']/row['answered'] if row['answered'] else 0
        row['budget_compliance']=1.;rows.append(row)
    with (OUT/'collision_summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print('Collision sensitivity completed:',sum(len(rs) for rs in groups.values()),'episodes.')
    for r in rows:
        if r['budget']==3 and r['policy'] in ('agreement','majority','dev_fixed'):print(r['regime'],r['policy'],r['correct'],r['wrong'],r['abstain'],r['calls'])
if __name__=='__main__':main()
