import unittest
from helpers import *
from llm_eval.utils import parse_commands_from_text, text_canonicalize, similarity

class TestUtils(unittest.TestCase):
    def test_parse_commands(self):
        txt = "$ echo hi\n\n```bash\nls\njob_tool status 42\n```\n"
        cmds = parse_commands_from_text(txt)
        self.assertIn('echo hi', cmds)
        self.assertIn('ls', cmds)
        self.assertIn('job_tool status 42', cmds)

    def test_similarity(self):
        a = 'line 1\n2025-10-10T20:01:12Z hi\n'
        b = 'line 1\n2025-10-11T10:02:12Z hi\n'
        self.assertGreaterEqual(similarity(text_canonicalize(a), text_canonicalize(b)), 0.9)

if __name__ == '__main__':
    unittest.main()
