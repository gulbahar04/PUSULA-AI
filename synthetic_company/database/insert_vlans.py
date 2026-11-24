
import json
import sqlite3

CONFIG_PATH = "synthetic_company/config/company_config.json"
DB_PATH = "synthetic_company/database/company.db"

# Lokasyonların ağ prefixleri
SITE_PREFIXES = {
    "IST": "10.20",
    "ANK": "10.30",
    "IZM": "10.40"
}

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    config = json.load(file)

vlan_definitions = config["network_infrastructure"]["vlan_definitions"]

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

inserted = 0

for site_id, prefix in SITE_PREFIXES.items():
    for vlan in vlan_definitions:

        vlan_id = vlan["vlan_id"]
        vlan_name = vlan["name"]
        subnet_octet = vlan["subnet_octet"]
        cidr = vlan["cidr"]

        subnet = f"{prefix}.{subnet_octet}.0/{cidr}"
        gateway = f"{prefix}.{subnet_octet}.1"
        dhcp_start = f"{prefix}.{subnet_octet}.50"
        dhcp_end = f"{prefix}.{subnet_octet}.230"

        cursor.execute("""
            INSERT OR IGNORE INTO vlans (
                vlan_id,
                site_id,
                vlan_name,
                subnet,
                gateway,
                dhcp_start,
                dhcp_end
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            vlan_id,
            site_id,
            vlan_name,
            subnet,
            gateway,
            dhcp_start,
            dhcp_end
        ))

        inserted += cursor.rowcount

conn.commit()

print("Yeni eklenen VLAN kaydı:", inserted)

print("\nLokasyonlara göre VLAN sayıları:")

for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM vlans
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

print("\nVLAN kayıtları:")

for row in cursor.execute("""
    SELECT site_id, vlan_id, vlan_name, subnet, gateway
    FROM vlans
    ORDER BY site_id, vlan_id
"""):
    print(row)

conn.close()
