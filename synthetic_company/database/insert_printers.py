
import sqlite3
import random

DB_PATH = "synthetic_company/database/company.db"

random.seed(42)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

site_counts = {
    "IST": 40,
    "ANK": 12,
    "IZM": 8
}

models = [
    ("HP", "LaserJet Enterprise M507"),
    ("HP", "LaserJet Pro M404"),
    ("Canon", "imageRUNNER ADVANCE DX"),
    ("Brother", "HL-L6400DW"),
    ("Xerox", "VersaLink B405")
]

# Departmanlara göre yazıcı dağılımı
departments = ["FIN", "HR", "SALES", "OPS", "MGMT"]

existing = cursor.execute(
    "SELECT COUNT(*) FROM printers"
).fetchone()[0]

if existing > 0:
    raise ValueError("Yazıcı kayıtları zaten mevcut.")

inserted = 0

for site_id, count in site_counts.items():

    prefix = {
        "IST": "10.20",
        "ANK": "10.30",
        "IZM": "10.40"
    }[site_id]

    for number in range(1, count + 1):

        printer_id = f"PRN{inserted + 1:03d}"
        hostname = f"{site_id}-PRN-{number:03d}"

        manufacturer, model = random.choice(models)

        # VLAN 160 için benzersiz IP
        ip_address = f"{prefix}.160.{50 + number}"

        mac_address = (
            f"02:DD:EE:"
            f"{inserted // 65536:02X}:"
            f"{inserted // 256 % 256:02X}:"
            f"{inserted % 256:02X}"
        )

        department_id = departments[
            (number - 1) % len(departments)
        ]

        printer_type = (
            "Multifunction"
            if number % 3 == 0
            else "Network Printer"
        )

        cursor.execute("""
            INSERT INTO printers (
                printer_id,
                hostname,
                manufacturer,
                model,
                site_id,
                department_id,
                ip_address,
                mac_address,
                vlan_id,
                printer_type,
                printer_status,
                last_inventory_update
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 160, ?, 'Active', ?)
        """, (
            printer_id,
            hostname,
            manufacturer,
            model,
            site_id,
            department_id,
            ip_address,
            mac_address,
            printer_type,
            "2026-11-20 09:00:00"
        ))

        inserted += 1

conn.commit()

print("Toplam eklenen yazıcı:", inserted)

print("\nLokasyon dağılımı:")
for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM printers
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

print("\nYazıcı IP adresi benzersizliği:")
print(cursor.execute("""
    SELECT COUNT(DISTINCT ip_address)
    FROM printers
""").fetchone()[0])

conn.close()
