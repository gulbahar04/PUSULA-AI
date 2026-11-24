
import sqlite3

DB_PATH = "synthetic_company/database/company.db"
DOMAIN = "ad.pusulaholding.local"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM dns_records"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"DNS tablosunda zaten {existing} kayıt var. İşlem durduruldu."
    )

sources = [
    ("computers", "ip_address", "device_status"),
    ("servers", "ip_address", "server_status"),
    ("printers", "ip_address", "printer_status"),
    ("ip_phones", "ip_address", "phone_status"),
    ("network_devices", "management_ip", "device_status"),
]

total = 0

for table, ip_column, status_column in sources:
    query = f"""
        SELECT hostname, {ip_column}, site_id, vlan_id
        FROM {table}
        WHERE {ip_column} IS NOT NULL
          AND hostname IS NOT NULL
          AND {status_column} = 'Active'
    """

    records = cursor.execute(query).fetchall()

    for hostname, ip_address, site_id, vlan_id in records:
        fqdn = f"{hostname.lower()}.{DOMAIN}"

        cursor.execute("""
            INSERT INTO dns_records (
                hostname, fqdn, record_type, ip_address,
                site_id, vlan_id, source_table, ttl, record_status
            )
            VALUES (?, ?, 'A', ?, ?, ?, ?, 3600, 'Active')
        """, (
            hostname, fqdn, ip_address,
            site_id, vlan_id, table
        ))

    total += len(records)
    print(f"{table}: {len(records)} DNS kaydı eklendi.")

conn.commit()

print("\nToplam DNS kaydı:", total)

conn.close()
