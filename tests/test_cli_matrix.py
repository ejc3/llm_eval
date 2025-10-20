import unittest, os, sys
from unittest.mock import patch
from helpers import *
import llm_eval.cli as cli
import yaml, tempfile

class TestMatrixCLI(unittest.TestCase):
    def test_matrix_invokes_runs(self):
        mat = {'dimensions': {'model': ['claude-3-5-sonnet'], 'tools_mode': ['mock'], 'engine': ['chat']}}
        with tempfile.NamedTemporaryFile('w', delete=False) as tf:
            yaml.safe_dump(mat, tf); tf.flush()
            with patch('llm_eval.cli.subprocess.run') as runmock:
                sys_argv = ['llm_eval', 'matrix', '--evals_glob', 'evals/*.md', '--matrix', tf.name]
                with patch.object(sys, 'argv', sys_argv):
                    self.assertEqual(cli.main(), 0)
                self.assertTrue(runmock.called)

if __name__ == '__main__':
    unittest.main()
