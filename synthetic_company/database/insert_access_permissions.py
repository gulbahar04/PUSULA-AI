
import sqlite3
from datetime import date

conn = sqlite3.connect("synthetic_company/database/company.db")

permissions = [
    ("G014", "FileServer", "FS01", "READ_WRITE"),
    ("G015", "FileServer", "FS01", "READ_WRITE"),
    ("G016", "FileServer", "FS01", "READ_ONLY"),
    ("G017", "ServerInfrastructure", "ALL_SERVERS", "ADMIN"),
    ("G007", "Application", "ERP", "USE"),
    ("G008", "Application", "CRM", "USE"),
    ("G009", "Application", "HR", "USE")
]

conn.executemany("""
    INSERT INTO access_permissions (
        group_id, resource_type, resource_id,
        permission_level, granted_date
    )
    VALUES (?, ?, ?, ?, ?)
""", [
    (*permission, date.today().isoformat())
    for permission in permissions
])

conn.commit()

print("Erişim izinleri:")
for row in conn.execute("""
    SELECT g.group_name, ap.resource_type,
           ap.resource_id, ap.permission_level
    FROM access_permissions ap
    JOIN ad_groups g ON ap.group_id = g.group_id
"""):
    print(row)

conn.close()
