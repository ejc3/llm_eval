import unittest, os
from helpers import *
from llm_eval.translator import translate_eval_md

class TestTranslator(unittest.TestCase):
    def test_job_monitor_translation(self):
        out = 'runtime/job_monitor.eval.yaml'
        data = translate_eval_md('evals/job_monitor.md', out, os.environ['LLM_CMD'])
        self.assertTrue(os.path.exists(out))
        allowed = data.get('guardrails', {}).get('allowed_tools', [])
        self.assertIn('job_tool', allowed)

    def test_canary_translation(self):
        out = 'runtime/canary_observe_readonly.eval.yaml'
        data = translate_eval_md('evals/canary_observe_readonly.md', out, os.environ['LLM_CMD'])
        self.assertTrue(os.path.exists(out))
        allowed = data.get('guardrails', {}).get('allowed_tools', [])
        self.assertIn('kubectl', allowed)

if __name__ == '__main__':
    unittest.main()
