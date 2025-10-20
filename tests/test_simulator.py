import unittest, os
from helpers import *
from llm_eval.simulator import simulate

class TestSimulator(unittest.TestCase):
    def test_job_tool_status(self):
        out = simulate('job_tool', 'job_tool status 42', 'evals/job_monitor.md', 'mocks/job_tool.md',
                       os.environ['LLM_CMD'], allow_help=False, shim_dir='.mock/bin', world_state_text='')
        self.assertIn('Status:', out)
        self.assertIn('SUCCEEDED', out)

    def test_kubectl_get(self):
        out = simulate('kubectl', 'kubectl get deploy web -n prod', 'evals/canary_observe_readonly.md', 'mocks/kubectl.md',
                       os.environ['LLM_CMD'], allow_help=False, shim_dir='.mock/bin', world_state_text='')
        self.assertIn('READY', out)
        self.assertIn('web', out)

if __name__ == '__main__':
    unittest.main()
