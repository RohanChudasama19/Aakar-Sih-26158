import os
import sys
sys.path.append(os.path.abspath("."))
from app.config import REDIS_URL
from app.main import queue_health
print("REDIS_URL is:", repr(REDIS_URL))
print("Queue health is:", queue_health())
