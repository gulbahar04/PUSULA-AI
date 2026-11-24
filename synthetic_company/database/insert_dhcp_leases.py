
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM dhcp_leases"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"DHCP tablosunda zaten {existing} kayıt var. "
        "İşlem durduruldu."
    )

# DHCP kullanacak cihazları bir araya getir
devices = []

# Bilgisayarlar
devices.extend(cursor.execute("""
    SELECT c.ip_address, c.mac_address, c.hostname,
           c.site_id, c.vlan_id
    FROM computers c
    WHERE c.ip_address IS NOT NULL
""").fetchall())

# Yazıcılar
devices.extend(cursor.execute("""
    SELECT ip_address, mac_address, hostname,
           site_id, vlan_id
    FROM printers
""").fetchall())

# IP telefonları
devices.extend(cursor.execute("""
    SELECT ip_address, mac_address, hostname,
           site_id, vlan_id
    FROM ip_phones
""").fetchall())

if len(devices) != 1510:
    raise ValueError(
        f"1510 cihaz bekleniyordu, bulunan: {len(devices)}"
    )

lease_start = datetime(2026, 11, 24, 8, 0, 0)
lease_end = lease_start + timedelta(hours=24)

for ip, mac, hostname, site_id, vlan_id in devices:

    cursor.execute("""
        INSERT INTO dhcp_leases (
            ip_address,
            mac_address,
            hostname,
            site_id,
            vlan_id,
            lease_start,
            lease_end,
            lease_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')
    """, (
        ip,
        mac,
        hostname,
        site_id,
        vlan_id,
        lease_start.strftime("%Y-%m-%d %H:%M:%S"),
        lease_end.strftime("%Y-%m-%d %H:%M:%S")
    ))

conn.commit()

print("Toplam DHCP kaydı:", len(devices))

print("\nLokasyon dağılımı:")
for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM dhcp_leases
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

print("\nVLAN dağılımı:")
for row in cursor.execute("""
    SELECT vlan_id, COUNT(*)
    FROM dhcp_leases
    GROUP BY vlan_id
    ORDER BY vlan_id
"""):
    print(row)

conn.close()
