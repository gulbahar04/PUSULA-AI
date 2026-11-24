
import sqlite3
import random

DB_PATH = "synthetic_company/database/company.db"

random.seed(42)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

site_counts = {
    "IST": 230,
    "ANK": 70,
    "IZM": 50
}

site_prefixes = {
    "IST": "10.20",
    "ANK": "10.30",
    "IZM": "10.40"
}

departments = ["FIN", "HR", "SALES", "OPS", "MGMT"]

models = [
    ("Cisco", "IP Phone 8841"),
    ("Yealink", "T46U"),
    ("Poly", "VVX 450")
]

existing = cursor.execute(
    "SELECT COUNT(*) FROM ip_phones"
).fetchone()[0]

if existing > 0:
    raise ValueError("IP telefon kayıtları zaten mevcut.")

inserted = 0

for site_id, count in site_counts.items():

    prefix = site_prefixes[site_id]

    for number in range(1, count + 1):

        phone_id = f"PHN{inserted + 1:04d}"
        hostname = f"{site_id}-PHONE-{number:03d}"

        manufacturer, model = random.choice(models)

        # VLAN 170 IP adresleri
        ip_address = f"{prefix}.170.{50 + number}"

        mac_address = (
            f"02:EE:FF:"
            f"{inserted // 65536:02X}:"
            f"{inserted // 256 % 256:02X}:"
            f"{inserted % 256:02X}"
        )

        department_id = departments[
            (number - 1) % len(departments)
        ]

        extension = f"{2000 + inserted}"

        cursor.execute("""
            INSERT INTO ip_phones (
                phone_id,
                hostname,
                manufacturer,
                model,
                site_id,
                department_id,
                ip_address,
                mac_address,
                vlan_id,
                phone_extension,
                phone_status,
                last_inventory_update
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 170, ?, 'Active', ?)
        """, (
            phone_id,
            hostname,
            manufacturer,
            model,
            site_id,
            department_id,
            ip_address,
            mac_address,
            extension,
            "2026-11-20 09:00:00"
        ))

        inserted += 1

conn.commit()

print("Toplam eklenen IP telefonu:", inserted)

print("\nLokasyon dağılımı:")

for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM ip_phones
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

print("\nBenzersiz IP adresi:", cursor.execute("""
    SELECT COUNT(DISTINCT ip_address)
    FROM ip_phones
""").fetchone()[0])

conn.close()
