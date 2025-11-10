import sqlite3, os
con = sqlite3.connect("worklaw.db")
cur = con.cursor()
cur.execute("SELECT year, amount, unit FROM minimum_wage WHERE year=2025")
print(cur.fetchone())
con.close()
