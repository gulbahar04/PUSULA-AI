
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

employees = conn.execute("""
    SELECT employee_id, first_name, last_name
    FROM employees
    ORDER BY employee_id
""").fetchall()

ad_users = []
now = datetime(2026, 11, 24, 10, 0, 0)

for index, (employee_id, first_name, last_name) in enumerate(employees[:1030], start=1):
    username = f"{first_name.lower()}.{last_name.lower()}.{index:04d}"
    account_status = "Enabled" if index <= 1000 else "Disabled"

    last_logon = now - timedelta(days=index % 30)
    password_last_set = now - timedelta(days=index % 90)

    ad_users.append((
        f"AD{index:04d}",
        employee_id,
        username,
        f"CN={username},OU=Users,DC=ad,DC=pusulaholding,DC=local",
        account_status,
        0,
        0,
        last_logon.isoformat(),
        password_last_set.isoformat()
    ))

conn.executemany("""
    INSERT INTO ad_users (
        ad_user_id, employee_id, username, distinguished_name,
        account_status, is_locked, is_privileged,
        last_logon, password_last_set
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ad_users)

conn.commit()

print("Toplam AD hesabı:", conn.execute(
    "SELECT COUNT(*) FROM ad_users"
).fetchone()[0])

print("\nHesap durumları:")
for row in conn.execute("""
    SELECT account_status, COUNT(*)
    FROM ad_users
    GROUP BY account_status
"""):
    print(row)

print("\nAD hesabı olmayan çalışan:", conn.execute("""
    SELECT COUNT(*)
    FROM employees e
    LEFT JOIN ad_users a ON e.employee_id = a.employee_id
    WHERE a.employee_id IS NULL
""").fetchone()[0])

conn.close()
