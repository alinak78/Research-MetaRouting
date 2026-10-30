"""Separate recovery study: actual numerical engines, injected faults, bounded calls.

Controllers cannot access the environment's fault schedule or evaluation target.
All policies consume the same response API and share paired fault interventions.
"""
from __future__ import annotations
import csv
import hashlib
import io
import math
import sqlite3
import time
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable
import numpy as np

ENGINES=('sqlite','python','numpy')
REGIMES=('clean','transient','persistent','independent','shifted','correlated')
BASE_POLICIES=('sql_only','python_only','numpy_only','retry','switch','agreement','majority')
POLICIES=BASE_POLICIES+('risk_gate','dev_fixed')
RISK={'count':.02,'sum':.12,'mean':.24,'max':.36}
THRESHOLDS=(0.,.05,.10,.20,1.)

@dataclass(frozen=True)
class Query:
    query_id: str
    split: str
    dataset: str
    operation: str
    target: int
    filter_column: int
    threshold: str

@dataclass(frozen=True)
class Response:
    engine: str
    status: str
    value: float | None


def close(a:float,b:float)->bool:
    return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-6)

def uniform(*parts)->float:
    return int.from_bytes(hashlib.sha256('|'.join(map(str,parts)).encode()).digest()[:8],'big')/2**64

class Dataset:
    def __init__(self,name:str,archive:Path):
        member={'iris':'iris.data','wine':'wine.data','banknote':'data_banknote_authentication.txt'}[name]
        with zipfile.ZipFile(archive) as z:
            records=list(csv.reader(io.StringIO(z.read(member).decode())))
        records=[r for r in records if r]
        self.strings=[r[1:] if name=='wine' else r[:-1] for r in records]
        self.rows=[[float(v) for v in row] for row in self.strings]
        self.array=np.asarray(self.rows)
        self.connection=sqlite3.connect(':memory:')
        cols=','.join(f'c{i} REAL' for i in range(self.array.shape[1]))
        self.connection.execute(f'CREATE TABLE records ({cols})')
        marks=','.join('?' for _ in range(self.array.shape[1]))
        self.connection.executemany(f'INSERT INTO records VALUES ({marks})',self.rows)
        self.connection.execute('PRAGMA query_only=ON')

    def queries(self,name:str,split:str)->list[Query]:
        qs=[]
        for op in RISK:
            for target in range(3):
                col=(target+1)%self.array.shape[1]
                ordered=sorted(Decimal(row[col]) for row in self.strings)
                for q in ([.25,.75] if split=='dev' else [.35,.65]):
                    threshold=str(ordered[int((len(ordered)-1)*q)])
                    qs.append(Query(f'{split}-{name}-{op}-{target}-{q}',split,name,op,target,col,threshold))
        return qs

    def reference(self,q:Query)->float:
        values=[Decimal(row[q.target]) for row in self.strings if Decimal(row[q.filter_column])>=Decimal(q.threshold)]
        if q.operation=='count':return float(len(values))
        if q.operation=='sum':return float(sum(values,Decimal(0)))
        if q.operation=='mean':return float(sum(values,Decimal(0))/len(values))
        return float(max(values))

    def execute(self,q:Query,engine:str,broken:bool=False)->float:
        if engine=='sqlite':
            agg={'count':'COUNT','sum':'SUM','mean':'AVG','max':'MAX'}[q.operation]
            table='unavailable_records' if broken else 'records'
            return float(self.connection.execute(f'SELECT {agg}(c{q.target}) FROM {table} WHERE c{q.filter_column} >= ?', (float(q.threshold),)).fetchone()[0])
        if engine=='python':
            values=[row[q.target] for row in self.rows if row[q.filter_column]>=float(q.threshold)]
            if q.operation=='count':return float(len(values))
            if q.operation=='sum':return float(math.fsum(values))
            if q.operation=='mean':return float(math.fsum(values)/len(values))
            return float(max(values))
        values=self.array[self.array[:,q.filter_column]>=float(q.threshold),q.target]
        return float({'count':lambda:len(values),'sum':lambda:np.sum(values),'mean':lambda:np.mean(values),'max':lambda:np.max(values)}[q.operation]())

class Environment:
    def __init__(self,dataset:Dataset,q:Query,regime:str,seed:int,budget:int):
        self.dataset=dataset;self.q=q;self.regime=regime;self.seed=seed;self.budget=budget
        self.steps=[];self.attempts=Counter()

    def call(self,engine:str)->Response:
        if len(self.steps)>=self.budget:raise RuntimeError('hard invocation budget exhausted')
        self.attempts[engine]+=1
        attempt=self.attempts[engine]
        broken=engine=='sqlite' and (self.regime=='persistent' or self.regime=='transient' and attempt==1)
        start=time.perf_counter_ns()
        fault='none'
        try:
            value=self.dataset.execute(self.q,engine,broken=broken)
            status='ok'
            scale=1. if self.regime!='shifted' else 2.
            if self.regime in ('independent','shifted'):
                rate=min(.95,RISK[self.q.operation]*{'sqlite':1.,'python':.5,'numpy':.4}[engine]*scale)
                if uniform(self.q.query_id,self.seed,engine,'silent')<rate:
                    value+= (5.,7.,11.)[ENGINES.index(engine)]
                    fault='independent_offset'
            elif self.regime=='correlated' and uniform(self.q.query_id,self.seed,'common')<.25:
                value+=7.
                fault='common_offset'
        except sqlite3.OperationalError:
            value=None;status='error';fault='missing_table'
        response=Response(engine,status,value)
        self.steps.append({**asdict(response),'attempt':attempt,'injected_fault':fault,
                           'elapsed_ms':(time.perf_counter_ns()-start)/1e6})
        return response


def agreement(values:list[float])->float|None:
    for value in values:
        if sum(close(value,other) for other in values)>=2:return value
    return None


def control(policy:str,q:Query,budget:int,call:Callable[[str],Response],risk:dict[str,float]|None=None,threshold:float=1.)->float|None:
    """The only controller interface: query, budget, observed responses, dev fit."""
    if policy.endswith('_only'):
        engine={'sql_only':'sqlite','python_only':'python','numpy_only':'numpy'}[policy]
        return call(engine).value
    if policy in ('retry','switch'):
        for i in range(budget):
            r=call('sqlite' if policy=='retry' else ENGINES[i])
            if r.status=='ok':return r.value
        return None
    if policy=='majority':
        values=[r.value for engine in ENGINES[:budget] if (r:=call(engine)).status=='ok']
        return values[0] if budget==1 and values else agreement(values)
    values=[]
    first=call('sqlite')
    if first.status=='ok':values.append(first.value)
    if budget==1:return first.value
    if policy=='risk_gate' and first.status=='ok' and risk[q.operation]<=threshold:
        return first.value
    for engine in ENGINES[1:budget]:
        r=call(engine)
        if r.status=='ok':values.append(r.value)
        match=agreement(values)
        if match is not None:return match
    # Explicit failures leave a single observed successful result; it is
    # accepted in recovery policies. Two conflicting results require abstention.
    return values[0] if len(values)==1 else None


def episode(dataset:Dataset,q:Query,regime:str,seed:int,budget:int,policy:str,risk=None,threshold=1.):
    env=Environment(dataset,q,regime,seed,budget)
    result=control(policy,q,budget,env.call,risk,threshold)
    gold=dataset.reference(q)
    correct=result is not None and close(result,gold)
    wrong=result is not None and not correct
    return {'query_id':q.query_id,'split':q.split,'dataset':q.dataset,'operation':q.operation,
            'regime':regime,'seed':seed,'budget':budget,'policy':policy,'correct':int(correct),
            'wrong':int(wrong),'abstain':int(result is None),'calls':len(env.steps),
            'utility':int(correct)-4*int(wrong)-.05*len(env.steps),'answer':result,'reference':gold,
            'execution_ms':sum(step['elapsed_ms'] for step in env.steps),'steps':env.steps}
