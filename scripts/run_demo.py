import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from misconception_aware_rag.core import grounded_response

docs={'d1':'Photosynthesis converts light energy into chemical energy.','d2':'Plants exchange gases through stomata.'}
misconceptions={'respiration_confusion':['plants do not respire']}
result=grounded_response('How does photosynthesis use light?', docs, misconceptions)
print('Detected misconceptions:', result['misconceptions'] or 'none')
print('Evidence IDs:', result['evidence_ids'])
print('Evidence:', result['evidence'])
