import os, json, hashlib, time
from .utils import ensure_dir

def now_ts_iso():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

class Trajectory:
    def __init__(self, path: str):
        self.path = path
        ensure_dir(os.path.dirname(path))
        with open(self.path, 'a', encoding='utf-8') as f:
            pass

    def write(self, obj: dict):
        obj = dict(obj)
        if 'ts' not in obj:
            obj['ts'] = now_ts_iso()
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj, ensure_ascii=False) + '\n')

    def sidecar_write(self, folder: str, text: str) -> str:
        ensure_dir(folder)
        h = hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()
        p = os.path.join(folder, h)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
        return h
