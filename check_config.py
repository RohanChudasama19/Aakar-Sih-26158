import sqlite3

conn = sqlite3.connect('data/3d0abc75-17af-4b1c-97e3-910c2fe56d06/work/colmap.db')
c = conn.cursor()

c.execute("SELECT config, count(*) FROM two_view_geometries GROUP BY config")
for row in c.fetchall():
    print(f"Config {row[0]}: {row[1]} pairs")
