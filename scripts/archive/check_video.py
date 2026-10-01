import json
with open('data/34c09ba6-a71d-4554-b86b-4b477295afda/work/outputs/mission_report.json') as f:
    r = json.load(f)
    print(r.get('input_info'))
