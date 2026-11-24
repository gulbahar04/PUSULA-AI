
import sqlite3
from collections import Counter

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# DHCP'ye dahil edilmesi gereken cihazlar
expected = []

queries = [
    """
    SELECT ip_address, mac_address, hostname, site_id, vlan_id
    FROM computers
    WHERE ip_address IS NOT NULL
    """,
    """
    SELECT ip_address, mac_address, hostname, site_id, vlan_id
    FROM printers
    """,
    """
    SELECT ip_address, mac_address, hostname, site_id, vlan_id
    FROM ip_phones
    """
]

for query in queries:
    expected.extend(cursor.execute(query).fetchall())

# DHCP kayıtları
actual = cursor.execute("""
    SELECT ip_address, mac_address, hostname, site_id, vlan_id
    FROM dhcp_leases
""").fetchall()

# Eksik veya fazladan kayıt kontrolü
missing = Counter(expected) - Counter(actual)
extra = Counter(actual) - Counter(expected)

# IP ve MAC çakışması kontrolü
duplicate_ips = [
    item for item, count in Counter(row[0] for row in actual).items()
    if count > 1
]

duplicate_macs = [
    item for item, count in Counter(row[1] for row in actual).items()
    if count > 1
]

# Lease süresi ve durum kontrolü
invalid_leases = cursor.execute("""
    SELECT COUNT(*)
    FROM dhcp_leases
    WHERE lease_status != 'Active'
       OR datetime(lease_end) <= datetime(lease_start)
""").fetchone()[0]

print("Beklenen cihaz sayısı:", len(expected))
print("DHCP kayıt sayısı:", len(actual))
print("Eksik kayıt:", sum(missing.values()))
print("Fazladan kayıt:", sum(extra.values()))
print("Tekrarlanan IP:", len(duplicate_ips))
print("Tekrarlanan MAC:", len(duplicate_macs))
print("Geçersiz lease:", invalid_leases)

if not missing and not extra and not duplicate_ips \
        and not duplicate_macs and invalid_leases == 0:
    print("\nSONUÇ: TÜM DHCP KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

    if duplicate_ips:
        print("Çakışan IP adresleri:", duplicate_ips)

    if duplicate_macs:
        print("Çakışan MAC adresleri:", duplicate_macs)

conn.close()
