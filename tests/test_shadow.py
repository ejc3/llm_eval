import unittest, os
from helpers import *
from llm_eval.runner import run_eval
from llm_eval.shadow import shadow_run

class TestShadow(unittest.TestCase):
    def test_shadow_reports(self):
        traj = run_eval('evals/job_monitor.md', tools_mode='mock', engine='chat', llm_cmd=os.environ['LLM_CMD'])
        rep = shadow_run(traj, sample=5, out_path=None)
        self.assertIn('results', rep)
        self.assertGreaterEqual(rep['checked'], 1)

if __name__ == '__main__':
    unittest.main()
