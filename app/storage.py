import os
from .config import DATA, S3_ENDPOINT, S3_BUCKET

def client():
    import boto3
    return boto3.client('s3', endpoint_url=S3_ENDPOINT, aws_access_key_id=os.environ['S3_ACCESS_KEY'], aws_secret_access_key=os.environ['S3_SECRET_KEY'])

def upload_job(job_id, directory):
    if not S3_ENDPOINT:
        return
    c = client()
    for p in sorted(directory.rglob('*')):
        if p.is_file():
            c.upload_file(str(p), S3_BUCKET, f'{job_id}/{p.relative_to(DATA / job_id).as_posix()}')
