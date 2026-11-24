
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")

groups = [
    # Department Global Groups
    ("G001", "GG-FINANCE-USERS", "Security", "Finance department users", 0, 0),
    ("G002", "GG-HR-USERS", "Security", "HR department users", 0, 0),
    ("G003", "GG-SALES-USERS", "Security", "Sales department users", 0, 0),
    ("G004", "GG-OPS-USERS", "Security", "Operations department users", 0, 0),
    ("G005", "GG-MANAGEMENT-USERS", "Security", "Management users", 0, 0),
    ("G006", "GG-IT-USERS", "Security", "IT department users", 0, 0),

    # Application Global Groups
    ("G007", "GG-ERP-USERS", "Security", "ERP application users", 0, 0),
    ("G008", "GG-CRM-USERS", "Security", "CRM application users", 0, 0),
    ("G009", "GG-HR-APP-USERS", "Security", "HR application users", 0, 0),

    # IT Role Groups
    ("G010", "GG-IT-SUPPORT", "Security", "IT support team", 0, 0),
    ("G011", "GG-SYSTEM-ADMINS", "Security", "System administrators", 1, 1),
    ("G012", "GG-NETWORK-ADMINS", "Security", "Network administrators", 1, 1),
    ("G013", "GG-SECURITY-ADMINS", "Security", "Security administrators", 1, 1),

    # Domain Local Groups
    ("G014", "DL-FS-FINANCE-RW", "Security", "Finance file read/write", 0, 0),
    ("G015", "DL-FS-HR-RW", "Security", "HR file read/write", 0, 0),
    ("G016", "DL-FS-SALES-RO", "Security", "Sales file read-only", 0, 0),
    ("G017", "DL-SERVER-MGMT", "Security", "Server management access", 1, 1),

    # Critical built-in group
    ("G018", "Domain Admins", "Security", "Active Directory domain administrators", 1, 1)
]

conn.executemany("""
    INSERT INTO ad_groups (
        group_id, group_name, group_type,
        description, is_privileged, is_critical
    )
    VALUES (?, ?, ?, ?, ?, ?)
""", groups)

conn.commit()

print("Toplam AD grubu:", conn.execute(
    "SELECT COUNT(*) FROM ad_groups"
).fetchone()[0])

print("\nGruplar:")
for row in conn.execute("""
    SELECT group_id, group_name, is_privileged, is_critical
    FROM ad_groups
"""):
    print(row)

conn.close()
