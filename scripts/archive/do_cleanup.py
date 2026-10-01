import os
import shutil
import sqlite3
import hashlib
from pathlib import Path

db_path = Path("app/aerorecon.db")
data_dir = Path("data").resolve()

# We only delete the specific approved ones
approved = [
    "206211f0-7407-4639-aab5-3adb49b6df03",
    "3f814df4-bb5b-4e00-ab07-ee6effd78d42",
    "5b85fba8-4e2b-4634-bac3-5a709f94bc1c",
    "9e6e5fc4-316d-4e92-bc56-0cb7bf72dacb",
    "b5eb3cc0-81b2-44fa-a6e7-f6d0a4b76750",
    "e1403ebf-70df-47ec-8f01-5e1285c66cb9",
    "FAST_VALIDATION",
    "test_benchmark",
    "95f51b12-b771-47bf-9201-c3700f9475a7" # Colorado - Wait, Colorado is a demo!
]
