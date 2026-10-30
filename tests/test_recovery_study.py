"""Checks of fault exposure, recovery, and the new hard-budget contract."""
from pathlib import Path
import unittest
from metarouter.recovery_study import Dataset,Environment,Query,Response,control,close,uniform
ROOT=Path(__file__).resolve().parents[1]

class RecoveryStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=Dataset('iris',ROOT/'benchmarks/recovery2027/raw/iris.zip')
        cls.q=cls.data.queries('iris','test')[0]

    def test_exception_consumes_budget(self):
        env=Environment(self.data,self.q,'persistent',0,1)
        self.assertEqual(env.call('sqlite').status,'error')
        with self.assertRaises(RuntimeError):env.call('python')
        self.assertEqual(len(env.steps),1)

    def test_retry_and_switch_have_different_persistent_outcomes(self):
        transient=Environment(self.data,self.q,'transient',0,2)
        self.assertTrue(close(control('retry',self.q,2,transient.call),self.data.reference(self.q)))
        persistent=Environment(self.data,self.q,'persistent',0,3)
        self.assertIsNone(control('retry',self.q,3,persistent.call))
        switch=Environment(self.data,self.q,'persistent',0,2)
        self.assertTrue(close(control('switch',self.q,2,switch.call),self.data.reference(self.q)))
        self.assertEqual(len(switch.steps),2)

    def test_disagreement_requires_third_engine_or_abstention(self):
        responses={'sqlite':Response('sqlite','ok',12.),'python':Response('python','ok',17.),'numpy':Response('numpy','ok',12.)}
        self.assertIsNone(control('agreement',self.q,2,responses.__getitem__))
        self.assertEqual(control('agreement',self.q,3,responses.__getitem__),12.)

    def test_common_corruption_can_pass_agreement(self):
        seed=next(s for s in range(1000) if uniform(self.q.query_id,s,'common')<.25)
        env=Environment(self.data,self.q,'correlated',seed,3)
        answer=control('agreement',self.q,3,env.call)
        self.assertFalse(close(answer,self.data.reference(self.q)))
        self.assertEqual(len(env.steps),2)
        self.assertTrue(all(r['injected_fault']=='common_offset' for r in env.steps))

    def test_faults_are_paired_across_call_order(self):
        a=Environment(self.data,self.q,'shifted',9,3)
        b=Environment(self.data,self.q,'shifted',9,3)
        ra=a.call('python');b.call('numpy');rb=b.call('python')
        self.assertEqual(ra,rb)

    def test_two_successes_after_primary_error_recover(self):
        env=Environment(self.data,self.q,'persistent',0,3)
        result=control('majority',self.q,3,env.call)
        self.assertTrue(close(result,self.data.reference(self.q)))

    def test_real_engines_agree_without_faults(self):
        for q in self.data.queries('iris','test'):
            for engine in ('sqlite','python','numpy'):
                self.assertTrue(close(self.data.execute(q,engine),self.data.reference(q)))

if __name__=='__main__':unittest.main()
