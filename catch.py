import sqlite3
conn = sqlite3.connect("submissions.db")
cur  = conn.cursor()
cur.execute("SELECT id, wpct, pf, pa, result FROM Submission;")
for row in cur.fetchall():
    print(row)
conn.close()
