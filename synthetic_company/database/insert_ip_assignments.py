
import sqlite3
import ipaddress
from datetime import datetime

DB_PATH = "synthetic_company/database/company.db"

# Departman - VLAN eşleşmesi
DEPARTMENT_VLANS = {
    "IT": 5,
    "FIN": 15,
    "HR": 25,
    "SALES": 35,
    "OPS": 45,
    "MGMT": 55
}

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Tekrar çalıştırılmasını önle
existing = cursor.execute(
    "SELECT COUNT(*) FROM ip_assignments"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"ip_assignments tablosunda zaten {existing} kayıt var. "
        "İşlem durduruldu."
    )

computers = cursor.execute("""
    SELECT computer_id, site_id, dept_id, device_type
    FROM computers
    ORDER BY computer_id
""").fetchall()

if len(computers) != 1100:
    raise ValueError(
        f"1100 bilgisayar bekleniyordu, bulunan: {len(computers)}"
    )

# VLAN bilgilerini lokasyon ve VLAN ID bazında al
vlan_rows = cursor.execute("""
    SELECT vlan_id, site_id, subnet, gateway,
           dhcp_start, dhcp_end
    FROM vlans
""").fetchall()

vlan_config = {
    (site_id, vlan_id): {
        "subnet": subnet,
        "gateway": gateway,
        "start": dhcp_start,
        "end": dhcp_end
    }
    for vlan_id, site_id, subnet, gateway,
        dhcp_start, dhcp_end in vlan_rows
}

# Her VLAN için kullanılabilir IP havuzu oluştur
ip_pools = {}

for key, config in vlan_config.items():
    start = int(ipaddress.ip_address(config["start"]))
    end = int(ipaddress.ip_address(config["end"]))

    ip_pools[key] = iter(range(start, end + 1))

assigned_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
inserted = 0

try:
    for computer_id, site_id, dept_id, device_type in computers:

        if device_type == "IT Workstation":
            vlan_id = 5
            site_id = "IST"
        else:
            if dept_id not in DEPARTMENT_VLANS:
                raise ValueError(
                    f"Bilinmeyen departman: {dept_id}"
                )
            vlan_id = DEPARTMENT_VLANS[dept_id]

        key = (site_id, vlan_id)

        if key not in vlan_config:
            raise ValueError(
                f"VLAN bulunamadı: {site_id}, VLAN {vlan_id}"
            )

        config = vlan_config[key]
        network = ipaddress.ip_network(config["subnet"])

        try:
            ip_number = next(ip_pools[key])
        except StopIteration:
            raise ValueError(
                f"DHCP havuzu doldu: {site_id}, VLAN {vlan_id}"
            )

        ip_address = str(ipaddress.ip_address(ip_number))

        cursor.execute("""
            INSERT INTO ip_assignments (
                computer_id, ip_address, subnet_mask,
                gateway, vlan_id, assignment_method,
                assigned_at, is_current
            )
            VALUES (?, ?, ?, ?, ?, 'DHCP', ?, 1)
        """, (
            computer_id,
            ip_address,
            str(network.netmask),
            config["gateway"],
            vlan_id,
            assigned_at
        ))

        cursor.execute("""
            UPDATE computers
            SET ip_address = ?, vlan_id = ?
            WHERE computer_id = ?
        """, (ip_address, vlan_id, computer_id))

        inserted += 1

    conn.commit()

except Exception:
    conn.rollback()
    raise

print("Toplam IP ataması:", inserted)

print("\nVLAN bazında bilgisayar dağılımı:")

for row in cursor.execute("""
    SELECT vlan_id, COUNT(*)
    FROM ip_assignments
    WHERE is_current = 1
    GROUP BY vlan_id
    ORDER BY vlan_id
"""):
    print(row)

print("\nLokasyon bazında IP dağılımı:")

for row in cursor.execute("""
    SELECT c.site_id, COUNT(*)
    FROM ip_assignments i
    JOIN computers c ON c.computer_id = i.computer_id
    WHERE i.is_current = 1
    GROUP BY c.site_id
    ORDER BY c.site_id
"""):
    print(row)

conn.close()
