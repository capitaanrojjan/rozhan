import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "rozhan.db")

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN wallet_balance INTEGER DEFAULT 0
    """)

    conn.commit()

    print("ستون کیف پول با موفقیت اضافه شد ✅")

except sqlite3.OperationalError as error:

    if "duplicate column name" in str(error):
        print("ستون کیف پول از قبل وجود دارد ✅")
    else:
        print("خطا:", error)

finally:
    conn.close()