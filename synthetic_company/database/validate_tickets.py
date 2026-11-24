
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

total = cursor.execute(
    "SELECT COUNT(*) FROM tickets"
).fetchone()[0]

invalid_employee = cursor.execute("""
    SELECT COUNT(*)
    FROM tickets t
    LEFT JOIN employees e ON t.employee_id = e.employee_id
    WHERE e.employee_id IS NULL
       OR e.employment_status != 'Active'
       OR e.site_id != t.site_id
""").fetchone()[0]

invalid_assignee = cursor.execute("""
    SELECT COUNT(*)
    FROM tickets t
    LEFT JOIN ad_users a
      ON t.assigned_ad_user_id = a.ad_user_id
    LEFT JOIN employees e ON a.employee_id = e.employee_id
    WHERE a.ad_user_id IS NULL
       OR a.account_status != 'Enabled'
       OR e.dept_id != 'IT'
""").fetchone()[0]

invalid_computer = cursor.execute("""
    SELECT COUNT(*)
    FROM tickets t
    JOIN computers c
      ON t.related_computer_id = c.computer_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM computer_assignments ca
        WHERE ca.computer_id = t.related_computer_id
          AND ca.employee_id = t.employee_id
          AND ca.assignment_status = 'Active'
    )
""").fetchone()[0]

invalid_dates = cursor.execute("""
    SELECT COUNT(*)
    FROM tickets
    WHERE updated_at < created_at
       OR (resolved_at IS NOT NULL AND resolved_at < created_at)
       OR (resolved_at IS NOT NULL AND resolved_at > updated_at)
""").fetchone()[0]

invalid_status = cursor.execute("""
    SELECT COUNT(*)
    FROM tickets
    WHERE status IN ('Resolved', 'Closed')
      AND resolved_at IS NULL
""").fetchone()[0]

checks = {
    "Toplam talep": total == 1000,
    "Geçersiz çalışan/lokasyon": invalid_employee == 0,
    "Geçersiz IT ataması": invalid_assignee == 0,
    "Geçersiz bilgisayar eşleşmesi": invalid_computer == 0,
    "Geçersiz tarihler": invalid_dates == 0,
    "Çözülme durumu tutarsızlığı": invalid_status == 0
}

print(f"Toplam destek talebi: {total}")
print(f"Geçersiz çalışan/lokasyon: {invalid_employee}")
print(f"Geçersiz IT ataması: {invalid_assignee}")
print(f"Geçersiz bilgisayar eşleşmesi: {invalid_computer}")
print(f"Geçersiz tarihler: {invalid_dates}")
print(f"Çözülme durumu tutarsızlığı: {invalid_status}")

print("\nSONUÇ:")
if all(checks.values()):
    print("TÜM TICKET KONTROLLERİ BAŞARILI.")
else:
    print("BAZI KONTROLLER BAŞARISIZ.")

conn.close()
