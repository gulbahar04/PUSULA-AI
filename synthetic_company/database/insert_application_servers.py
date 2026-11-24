
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

servers = {
    hostname: server_id
    for server_id, hostname in cursor.execute("""
        SELECT server_id, hostname FROM servers
    """).fetchall()
}

applications = [
    # ERP
    ("ERP", "ERP01", "Primary Application Server"),
    ("ERP", "ERP02", "Secondary Application Server"),
    ("ERP", "SQL01", "Database Server"),

    # CRM
    ("CRM", "CRM01", "Primary Application Server"),
    ("CRM", "CRM02", "Integration Server"),
    ("CRM", "CRM03", "Reporting Server"),
    ("CRM", "CRM04", "API Server"),
    ("CRM", "SQL02", "Database Server"),

    # HR
    ("HR", "HR01", "Primary Application Server"),
    ("HR", "HR02", "Document Server"),
    ("HR", "HR03", "Integration Server"),
    ("HR", "SQL03", "Database Server"),

    # FILE
    ("FILE", "FS01", "Primary File Server"),
    ("FILE", "FS02", "Department File Server"),
]

existing = cursor.execute(
    "SELECT COUNT(*) FROM application_servers"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        "Uygulama-sunucu kayıtları zaten mevcut. İşlem durduruldu."
    )

for app_name, hostname, role in applications:

    if hostname not in servers:
        raise ValueError(f"Sunucu bulunamadı: {hostname}")

    cursor.execute("""
        INSERT INTO application_servers (
            application_name,
            server_id,
            server_role
        )
        VALUES (?, ?, ?)
    """, (
        app_name,
        servers[hostname],
        role
    ))

conn.commit()

print("Eklenen uygulama-sunucu eşleştirmesi:", len(applications))

print("\nUygulama dağılımı:")

for row in cursor.execute("""
    SELECT application_name, COUNT(*)
    FROM application_servers
    GROUP BY application_name
    ORDER BY application_name
"""):
    print(row)

conn.close()
