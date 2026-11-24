
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

servers = [
    # Identity & Network (6)
    ("DC01", "Identity & Network", "Primary Domain Controller", "10.20.100.10", "Critical"),
    ("DC02", "Identity & Network", "Secondary Domain Controller", "10.20.100.11", "Critical"),
    ("DHCP01", "Identity & Network", "DHCP Server", "10.20.100.60", "High"),
    ("DNS01", "Identity & Network", "DNS Server", "10.20.100.61", "Critical"),
    ("NPS01", "Identity & Network", "Network Policy Server", "10.20.100.62", "High"),
    ("ADCS01", "Identity & Network", "Certificate Authority", "10.20.100.63", "High"),

    # File Servers (4)
    ("FS01", "File Servers", "Primary File Server", "10.20.100.20", "High"),
    ("FS02", "File Servers", "Department File Server", "10.20.100.21", "High"),
    ("FS03", "File Servers", "Archive File Server", "10.20.100.22", "Medium"),
    ("FS04", "File Servers", "Backup File Server", "10.20.100.23", "Medium"),

    # ERP & Database (6)
    ("ERP01", "ERP & Database", "ERP Application Server", "10.20.100.30", "Critical"),
    ("SQL01", "ERP & Database", "ERP Database Server", "10.20.100.31", "Critical"),
    ("SQL02", "ERP & Database", "CRM Database Server", "10.20.100.32", "Critical"),
    ("SQL03", "ERP & Database", "HR Database Server", "10.20.100.33", "High"),
    ("ERP02", "ERP & Database", "ERP Application Secondary", "10.20.100.34", "High"),
    ("DBMON01", "ERP & Database", "Database Monitoring Server", "10.20.100.35", "Medium"),

    # CRM (4)
    ("CRM01", "CRM", "CRM Application Server", "10.20.100.40", "Critical"),
    ("CRM02", "CRM", "CRM Integration Server", "10.20.100.41", "High"),
    ("CRM03", "CRM", "CRM Reporting Server", "10.20.100.42", "Medium"),
    ("CRM04", "CRM", "CRM API Server", "10.20.100.43", "High"),

    # HR Systems (3)
    ("HR01", "HR Systems", "HR Application Server", "10.20.100.50", "High"),
    ("HR02", "HR Systems", "HR Document Server", "10.20.100.51", "Medium"),
    ("HR03", "HR Systems", "HR Integration Server", "10.20.100.52", "Medium"),

    # Backup (3)
    ("BACKUP01", "Backup", "Primary Backup Server", "10.20.100.80", "Critical"),
    ("BACKUP02", "Backup", "Secondary Backup Server", "10.20.100.81", "High"),
    ("BACKUP03", "Backup", "Backup Repository Server", "10.20.100.82", "High"),

    # Monitoring (3)
    ("MON01", "Monitoring", "Infrastructure Monitoring", "10.20.100.90", "High"),
    ("MON02", "Monitoring", "Log Management Server", "10.20.100.91", "High"),
    ("MON03", "Monitoring", "Performance Monitoring", "10.20.100.92", "Medium"),

    # Security (4)
    ("SIEM01", "Security", "SIEM Server", "10.20.100.100", "Critical"),
    ("EDR01", "Security", "Endpoint Detection Server", "10.20.100.101", "Critical"),
    ("AV01", "Security", "Antivirus Management Server", "10.20.100.102", "High"),
    ("VULN01", "Security", "Vulnerability Management Server", "10.20.100.103", "High"),

    # Other Infrastructure (7)
    ("WSUS01", "Other Infrastructure", "Windows Update Server", "10.20.100.70", "High"),
    ("PRINT01", "Other Infrastructure", "Print Management Server", "10.20.100.71", "Medium"),
    ("VPN01", "Other Infrastructure", "VPN Gateway Server", "10.20.100.72", "Critical"),
    ("APP01", "Other Infrastructure", "Internal Application Server", "10.20.100.73", "Medium"),
    ("WEB01", "Other Infrastructure", "Internal Web Server", "10.20.100.74", "Medium"),
    ("MECM01", "Other Infrastructure", "Endpoint Management Server", "10.20.100.75", "High"),
    ("FILEIDX01", "Other Infrastructure", "File Indexing Server", "10.20.100.76", "Low"),
]

if len(servers) != 40:
    raise ValueError(f"40 sunucu bekleniyordu, bulunan: {len(servers)}")

existing = cursor.execute(
    "SELECT COUNT(*) FROM servers"
).fetchone()[0]

if existing > 0:
    raise ValueError("Sunucu tablosunda zaten kayıt var. İşlem durduruldu.")

for index, server in enumerate(servers, start=1):
    hostname, category, role, ip, criticality = server

    cursor.execute("""
        INSERT INTO servers (
            server_id, hostname, server_category,
            server_role, operating_system, site_id,
            ip_address, vlan_id, environment,
            server_status, criticality, last_inventory_update
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"SRV{index:03d}",
        hostname,
        category,
        role,
        "Windows Server 2022",
        "IST",
        ip,
        100,
        "Production",
        "Active",
        criticality,
        "2026-11-20 09:00:00"
    ))

conn.commit()

print("Toplam sunucu:", len(servers))
print("\nKategori dağılımı:")

for row in cursor.execute("""
    SELECT server_category, COUNT(*)
    FROM servers
    GROUP BY server_category
    ORDER BY server_category
"""):
    print(row)

print("\nSunucu IP kontrolü:")
print("Benzersiz IP:", cursor.execute(
    "SELECT COUNT(DISTINCT ip_address) FROM servers"
).fetchone()[0])

conn.close()
