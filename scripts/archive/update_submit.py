import sys
code = open('app/main.py', encoding='utf-8').read()
import re
new_params = '''    rtk: UploadFile | None = File(None),
    segmentation: UploadFile | None = File(None),
    depth: UploadFile | None = File(None),
    project_id: str = Form("default-legacy-project"),'''

code = re.sub(
    r'rtk: UploadFile \| None = File\(None\),\s*segmentation: UploadFile \| None = File\(None\),\s*depth: UploadFile \| None = File\(None\),',
    new_params,
    code,
    count=1
)

# inject checking project existence
check_proj = '''    if segmentation and os.getenv("ALLOW_TRUSTED_PT", "0") != "1":
        raise HTTPException(
            422,
            "Custom PT loading is disabled. Only an administrator may enable trusted checkpoint loading; PT files can execute code.",
        )
    
    with Session.begin() as s:
        from .db import Project
        if not s.get(Project, project_id):
            raise HTTPException(422, "Project does not exist")
'''
code = re.sub(r'if segmentation and os.getenv.*?execute code\.",\n\s*\)', check_proj, code, count=1, flags=re.DOTALL)

# inject job creation with project_id
create_job = '''    with Session.begin() as s:
        j = Job(id=jid, project_id=project_id, name=name, options=opts)'''
code = re.sub(r'with Session\.begin\(\) as s:\n\s*j = Job\(id=jid, name=name, options=opts\)', create_job, code, count=1)

with open('app/main.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated submit to accept project_id")
