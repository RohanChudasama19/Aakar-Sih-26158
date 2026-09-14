import os
import tempfile
os.environ['DATA_DIR']=tempfile.mkdtemp(prefix='aerorecon-tests-')
os.environ['REDIS_URL']=''
os.environ['S3_ENDPOINT']=''
os.environ['API_TOKEN']=''
