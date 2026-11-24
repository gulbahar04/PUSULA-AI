
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("synthetic_company/database/company.db")

employees = conn.execute("""
    SELECT employee_id, first_name, last_name
    FROM employees
    ORDER BY employee_id
""").fetchall()

accounts = []
now = datetime(2026, 11, 24, 10, 0, 0)

for index, (employee_id, first_name, last_name) in enumerate(employees[:1020], start=1):
    email = f"{first_name.lower()}.{last_name.lower()}.{index:04d}@pusulaholding.com"

    status = "Active" if index <= 990 else "Disabled"
    mfa_enabled = 1 if index % 10 != 0 else 0

    license_type = "Business_Premium" if index % 3 == 0 else "Business_Standard"

    accounts.append((
        f"M365{index:04d}",
        employee_id,
        email,
        status,
        license_type,
        mfa_enabled,
        (now - timedelta(days=index % 365)).date().isoformat(),
        (now - timedelta(days=index % 30)).isoformat()
    ))

conn.executemany("""
    INSERT INTO m365_accounts (
        m365_account_id, employee_id, email, account_status,
        license_type, mfa_enabled, created_date, last_signin
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", accounts)

conn.commit()

print("Toplam M365 hesabı:",
      conn.execute("SELECT COUNT(*) FROM m365_accounts").fetchone()[0])

print("\nHesap durumları:")
for row in conn.execute("""
    SELECT account_status, COUNT(*)
    FROM m365_accounts
    GROUP BY account_status
"""):
    print(row)

print("\nMFA durumları:")
for row in conn.execute("""
    SELECT mfa_enabled, COUNT(*)
    FROM m365_accounts
    GROUP BY mfa_enabled
"""):
    print(row)

print("\nM365 hesabı olmayan çalışan:",
      conn.execute("""
          SELECT COUNT(*)
          FROM employees e
          LEFT JOIN m365_accounts m ON e.employee_id = m.employee_id
          WHERE m.employee_id IS NULL
      """).fetchone()[0])

conn.close()
