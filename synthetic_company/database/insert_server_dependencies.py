
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Sunucu adlarını ID'leriyle eşleştir
servers = {
    hostname: server_id
    for server_id, hostname in cursor.execute("""
        SELECT server_id, hostname FROM servers
    """).fetchall()
}

dependencies = [
    # ERP bağımlılıkları
    ("ERP01", "SQL01", "Database"),
    ("ERP01", "DC01", "Authentication"),
    ("ERP01", "DNS01", "DNS"),

    # CRM bağımlılıkları
    ("CRM01", "SQL02", "Database"),
    ("CRM01", "DC01", "Authentication"),
    ("CRM01", "DNS01", "DNS"),

    # HR bağımlılıkları
    ("HR01", "SQL03", "Database"),
    ("HR01", "DC01", "Authentication"),
    ("HR01", "DNS01", "DNS"),

    # Diğer altyapı bağımlılıkları
    ("FS01", "DC01", "Authentication"),
    ("FS01", "DNS01", "DNS"),
    ("WSUS01", "DC01", "Authentication"),
    ("WSUS01", "DNS01", "DNS"),
]

existing = cursor.execute(
    "SELECT COUNT(*) FROM server_dependencies"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        "Bağımlılık kayıtları zaten mevcut. İşlem durduruldu."
    )

for source, target, dependency_type in dependencies:

    if source not in servers or target not in servers:
        raise ValueError(
            f"Sunucu bulunamadı: {source} veya {target}"
        )

    description = (
        f"{source}, {target} servisine "
        f"{dependency_type} amacıyla bağımlıdır."
    )

    cursor.execute("""
        INSERT INTO server_dependencies (
            source_server_id,
            target_server_id,
            dependency_type,
            description
        )
        VALUES (?, ?, ?, ?)
    """, (
        servers[source],
        servers[target],
        dependency_type,
        description
    ))

conn.commit()

print("Eklenen bağımlılık sayısı:", len(dependencies))

print("\nBağımlılık kayıtları:")

for row in cursor.execute("""
    SELECT
        s1.hostname,
        d.dependency_type,
        s2.hostname
    FROM server_dependencies d
    JOIN servers s1
        ON d.source_server_id = s1.server_id
    JOIN servers s2
        ON d.target_server_id = s2.server_id
    ORDER BY s1.hostname
"""):
    print(row)

conn.close()
