
import sqlite3
import random

DB_PATH = "synthetic_company/database/company.db"

random.seed(42)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

site_config = {
    "IST": {"prefix": "10.20", "counts": {
        "Switch": 12, "Router": 2,
        "Firewall": 2, "Access Point": 20
    }},
    "ANK": {"prefix": "10.30", "counts": {
        "Switch": 4, "Router": 1,
        "Firewall": 1, "Access Point": 7
    }},
    "IZM": {"prefix": "10.40", "counts": {
        "Switch": 3, "Router": 1,
        "Firewall": 1, "Access Point": 6
    }}
}

models = {
    "Switch": ("Cisco", "Catalyst 9300"),
    "Router": ("Cisco", "ISR 4331"),
    "Firewall": ("Fortinet", "FortiGate 100F"),
    "Access Point": ("Cisco", "Catalyst 9115AXI")
}

existing = cursor.execute(
    "SELECT COUNT(*) FROM network_devices"
).fetchone()[0]

if existing > 0:
    raise ValueError("Ağ cihazları zaten mevcut. İşlem durduruldu.")

inserted = 0

for site_id, config in site_config.items():

    prefix = config["prefix"]

    for device_type, count in config["counts"].items():

        manufacturer, model = models[device_type]

        for number in range(1, count + 1):

            device_id = f"NET{inserted + 1:03d}"
            hostname = (
                f"{site_id}-"
                f"{device_type.upper().replace(' ', '-')}-"
                f"{number:03d}"
            )

            # Yönetim VLAN 150
            ip_address = f"{prefix}.150.{50 + inserted % 180}"

            mac_address = (
                f"02:FF:AA:"
                f"{inserted // 65536:02X}:"
                f"{inserted // 256 % 256:02X}:"
                f"{inserted % 256:02X}"
            )

            cursor.execute("""
                INSERT INTO network_devices (
                    device_id, hostname, device_type,
                    manufacturer, model, site_id,
                    management_ip, mac_address, vlan_id,
                    device_status, last_inventory_update
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 150, 'Active', ?)
            """, (
                device_id,
                hostname,
                device_type,
                manufacturer,
                model,
                site_id,
                ip_address,
                mac_address,
                "2026-11-20 09:00:00"
            ))

            inserted += 1

conn.commit()

print("Toplam ağ cihazı:", inserted)

print("\nCihaz türlerine göre dağılım:")
for row in cursor.execute("""
    SELECT device_type, COUNT(*)
    FROM network_devices
    GROUP BY device_type
    ORDER BY device_type
"""):
    print(row)

print("\nLokasyon dağılımı:")
for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM network_devices
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

print("\nBenzersiz yönetim IP sayısı:")
print(cursor.execute("""
    SELECT COUNT(DISTINCT management_ip)
    FROM network_devices
""").fetchone()[0])

conn.close()
