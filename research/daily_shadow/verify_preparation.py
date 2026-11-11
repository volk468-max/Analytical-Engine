"""Rebuild all frozen artifacts offline; preserve every published version."""
from unittest.mock import patch
from .artifacts import OUT,build
from .core import sha
from .coverage import report

def verify():
 before=sha((OUT/'model-index.json').read_bytes())
 with patch('socket.socket',side_effect=AssertionError('NETWORK_FORBIDDEN')):models=build()
 assert len(models)==222
 assert before==sha((OUT/'model-index.json').read_bytes()),'MODEL_ARTIFACT_REPLAY_MISMATCH'
 summary=report();assert summary['genuine_live_probabilities']==0 and summary['null_probabilities']==222
 print('222 frozen artifacts reproduced; no qualified live probability; network forbidden: PASS')
if __name__=='__main__':verify()
