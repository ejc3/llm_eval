import unittest, os
from helpers import *
from llm_eval.runner import run_eval
from llm_eval.grader import grade_trajectory

class TestEndToEnd(unittest.TestCase):
    def test_job_monitor_passes(self):
        traj = run_eval('evals/job_monitor.md', tools_mode='mock', engine='chat', llm_cmd=os.environ['LLM_CMD'])
        self.assertTrue(os.path.exists(traj))
        eval_yaml = 'runtime/job_monitor.eval.yaml'
        res = grade_trajectory(traj, eval_yaml)
        self.assertEqual(res['verdict'], 'PASS')

    def test_canary_runs(self):
        traj = run_eval('evals/canary_observe_readonly.md', tools_mode='mock', engine='chat', llm_cmd=os.environ['LLM_CMD'])
        self.assertTrue(os.path.exists(traj))
        eval_yaml = 'runtime/canary_observe_readonly.eval.yaml'
        res = grade_trajectory(traj, eval_yaml)
        self.assertIn(res['verdict'], ['PASS','SOFT_PASS','INCONCLUSIVE'])

if __name__ == '__main__':
    unittest.main()
