import sqlite3

conn = sqlite3.connect("rozhan.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    image TEXT
)
""")

conn.commit()
conn.close()

print("جدول محصولات با موفقیت ساخته شد ✅")