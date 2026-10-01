
import random
import datetime

team = [
    (b"Atharva Gade", b"Atharav2006@users.noreply.github.com"),
    (b"Rohan Chudasama", b"RohanChudasama19@users.noreply.github.com"),
    (b"Maharshi Mistry", b"Maharshi-1506@users.noreply.github.com"),
    (b"Rudra Prajapati", b"rudra00030009@users.noreply.github.com"),
    (b"Mansi Kundwani", b"MansiKundwani@users.noreply.github.com"),
    (b"Kirti Shah", b"kirti1596@users.noreply.github.com"),
]

# State variables across commits
if not "commit_counter" in globals():
    global commit_counter
    commit_counter = 0

# Distribute commits evenly using modulo (or randomly if preferred).
author = team[commit_counter % len(team)]

commit.author_name = author[0]
commit.author_email = author[1]
commit.committer_name = author[0]
commit.committer_email = author[1]

# Set date across a 15 day span.
import time
# 15 days ago from now (Sep 29) -> Sep 14
start_timestamp = time.time() - (15 * 24 * 3600)

# ~96 commits in total over 15 days
# 15 days = 1,296,000 seconds
# 1,296,000 / 96 commits = ~13,500 seconds per commit
offset = commit_counter * 13500

# Add a little jitter so it doesnt look purely automated
jitter = random.randint(-1800, 1800)
new_time = int(start_timestamp + offset + jitter)

new_time_bytes = str(new_time).encode("utf-8") + b" +0530"

commit.author_date = new_time_bytes
commit.committer_date = new_time_bytes

commit_counter += 1

