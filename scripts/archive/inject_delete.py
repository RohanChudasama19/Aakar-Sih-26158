code = open('app/main.py', encoding='utf-8').read()
if '@app.delete("/api/jobs/{jid}")' not in code:
    delete_job = '''
@app.delete("/api/jobs/{jid}")
def delete_job(jid: str):
    with Session.begin() as s:
        j = s.get(Job, jid)
        if not j:
            raise HTTPException(404, "Job not found")
        s.delete(j)
        # Rename directory instead of hard delete
        work_dir = DATA / jid / "work"
        if work_dir.exists():
            deleted_dir = DATA / f"deleted_{jid}"
            try:
                work_dir.rename(deleted_dir)
            except Exception:
                pass
        return {"status": "deleted"}
'''
    import re
    code = re.sub(r'(@app\.get\("/api/jobs"\))', delete_job + r'\n\n\1', code, count=1)
    with open('app/main.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Added delete job endpoint")
else:
    print("Delete job endpoint already exists")
