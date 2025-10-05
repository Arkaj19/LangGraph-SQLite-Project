import sqlite3

conn = sqlite3.connect("desserts.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(indian_desserts);")
for col in cursor.fetchall():
    print(col)

conn.close()

