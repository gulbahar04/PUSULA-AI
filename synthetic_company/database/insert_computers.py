
import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "synthetic_company/database/company.db"

random.seed(42)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

employees = cursor.execute("""
    SELECT employee_id, dept_id, site_id
    FROM employees
    ORDER BY employee_id
""").fetchall()

if len(employees) != 1050:
    raise ValueError(f"Beklenen 1050 çalışan, bulunan: {len(employees)}")

laptop_employees = set(
    employee[0] for employee in random.sample(employees, 650)
)

models = {
    "Laptop": [
        ("Dell", "Latitude 5440"),
        ("HP", "ProBook 450 G10"),
        ("Lenovo", "ThinkPad E14")
    ],
    "Desktop": [
        ("Dell", "OptiPlex 7010"),
        ("HP", "ProDesk 400 G9"),
        ("Lenovo", "ThinkCentre M70")
    ],
    "IT Workstation": [
        ("Dell", "Precision 3660"),
        ("HP", "Z2 Tower G9"),
        ("Lenovo", "ThinkStation P3")
    ]
}

counters = {}
inserted = 0

def generate_mac(number):
    return f"02:PU:{number:02X}:AA:BB:CC"

# Çalışanlara birer bilgisayar
for index, (employee_id, dept_id, site_id) in enumerate(employees, start=1):

    device_type = (
        "Laptop" if employee_id in laptop_employees else "Desktop"
    )

    manufacturer, model = random.choice(models[device_type])

    type_code = "LT" if device_type == "Laptop" else "PC"
    key = (site_id, dept_id, type_code)
    counters[key] = counters.get(key, 0) + 1

    hostname = (
        f"{site_id}-{dept_id}-{type_code}-{counters[key]:03d}"
    )

    computer_id = f"PC{index:04d}"
    serial_number = f"PUSULA-SN-{index:05d}"

    purchase_date = (
        date(2021, 1, 1) +
        timedelta(days=random.randint(0, 1800))
    )

    ou_type = "Laptops" if device_type == "Laptop" else "Workstations"
    ou_path = (
        f"OU={ou_type},OU=Computers,"
        "DC=ad,DC=pusulaholding,DC=local"
    )

    cursor.execute("""
        INSERT INTO computers (
            computer_id, hostname, serial_number,
            manufacturer, model, device_type,
            operating_system, site_id, dept_id,
            mac_address, ou_path, device_status,
            purchase_date, last_inventory_update
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        computer_id,
        hostname,
        serial_number,
        manufacturer,
        model,
        device_type,
        "Windows 11 Pro",
        site_id,
        dept_id,
        f"02:AA:BB:{index // 65536:02X}:{index // 256 % 256:02X}:{index % 256:02X}",
        ou_path,
        "Active",
        purchase_date.isoformat(),
        "2026-11-20 09:00:00"
    ))

    inserted += 1

# IT için 50 ek workstation
for number in range(1, 51):

    manufacturer, model = random.choice(models["IT Workstation"])
    computer_id = f"PC{1050 + number:04d}"

    cursor.execute("""
        INSERT INTO computers (
            computer_id, hostname, serial_number,
            manufacturer, model, device_type,
            operating_system, site_id, dept_id,
            mac_address, ou_path, device_status,
            purchase_date, last_inventory_update
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        computer_id,
        f"IST-IT-WS-{number:03d}",
        f"PUSULA-SN-{1050 + number:05d}",
        manufacturer,
        model,
        "IT Workstation",
        "Windows 11 Pro",
        "IST",
        "IT",
        f"02:CC:DD:{number // 65536:02X}:{number // 256 % 256:02X}:{number % 256:02X}",
        "OU=Workstations,OU=Computers,DC=ad,DC=pusulaholding,DC=local",
        "Active",
        "2025-01-15",
        "2026-11-20 09:00:00"
    ))

    inserted += 1

conn.commit()

print(f"Toplam eklenen bilgisayar: {inserted}")
print("\nCihaz türlerine göre dağılım:")

for row in cursor.execute("""
    SELECT device_type, COUNT(*)
    FROM computers
    GROUP BY device_type
    ORDER BY device_type
"""):
    print(row)

conn.close()
