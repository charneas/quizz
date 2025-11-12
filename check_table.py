import sqlite3

conn = sqlite3.connect('quiz.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(game)")
columns = cursor.fetchall()
print("\nGame table structure:")
for column in columns:
    print(f"Column: {column[1]}, Type: {column[2]}")
conn.close()
