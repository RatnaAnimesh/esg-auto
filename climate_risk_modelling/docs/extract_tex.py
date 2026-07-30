import json

log_path = '/Users/ashishmishra/.gemini/antigravity-ide/brain/a6528cc0-97f4-40ce-8fae-345110ce3164/.system_generated/logs/transcript.jsonl'

best_content = None

with open(log_path, 'r') as f:
    for line in f:
        data = json.loads(line)
        if 'tool_calls' in data:
            for tc in data['tool_calls']:
                if tc['name'] == 'write_to_file':
                    args = tc.get('args', {})
                    if 'climate_risk_model_technical_methodology.tex' in args.get('TargetFile', '') or 'climate_risk_model_report.tex' in args.get('TargetFile', ''):
                        best_content = args.get('CodeContent')

if best_content:
    if best_content.startswith('"') and best_content.endswith('"'):
        best_content = best_content[1:-1]
    
    # decode escaped characters like \n
    best_content = best_content.encode('utf-8').decode('unicode_escape')
    
    with open('climate_risk_model_report.tex', 'w') as out:
        out.write(best_content)
    print("Recovered from write_to_file TargetFile")
