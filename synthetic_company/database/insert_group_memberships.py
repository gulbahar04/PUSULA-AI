
import sqlite3
from datetime import date

conn = sqlite3.connect("synthetic_company/database/company.db")

# Departman -> AD grup eşleşmeleri
department_groups = {
    "FIN": "G001",
    "HR": "G002",
    "SALES": "G003",
    "OPS": "G004",
    "MGMT": "G005",
    "IT": "G006"
}

# Departman -> uygulama grubu eşleşmeleri
application_groups = {
    "FIN": ["G007"],
    "SALES": ["G008"],
    "HR": ["G009"]
}

memberships = []

users = conn.execute("""
    SELECT a.ad_user_id, e.dept_id
    FROM ad_users a
    JOIN employees e ON a.employee_id = e.employee_id
    WHERE a.account_status = 'Enabled'
""").fetchall()

for ad_user_id, dept_id in users:
    # Departman grubu
    group_id = department_groups.get(dept_id)
    if group_id:
        memberships.append((ad_user_id, group_id, date.today().isoformat()))

    # Uygulama grupları
    for app_group_id in application_groups.get(dept_id, []):
        memberships.append((ad_user_id, app_group_id, date.today().isoformat()))

conn.executemany("""
    INSERT INTO group_memberships (
        ad_user_id, group_id, membership_date
    )
    VALUES (?, ?, ?)
""", memberships)

conn.commit()

print("Toplam grup üyeliği:", conn.execute(
    "SELECT COUNT(*) FROM group_memberships"
).fetchone()[0])

print("\nGrup bazında üye sayıları:")
for row in conn.execute("""
    SELECT g.group_name, COUNT(gm.ad_user_id)
    FROM ad_groups g
    LEFT JOIN group_memberships gm ON g.group_id = gm.group_id
    GROUP BY g.group_id
    ORDER BY g.group_id
"""):
    print(row)

conn.close()
