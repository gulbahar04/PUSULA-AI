
import sqlite3
from collections import Counter

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

expected_sources = {
    "computers": 1100,
    "servers": 40,
    "printers": 60,
    "ip_phones": 350,
    "network_devices": 60,
}

total = cursor.execute(
    "SELECT COUNT(*) FROM dns_records"
).fetchone()[0]

print("Toplam DNS kaydı:", total)

print("\nKaynak tablo dağılımı:")
source_counts = dict(cursor.execute("""
    SELECT source_table, COUNT(*)
    FROM dns_records
    GROUP BY source_table
""").fetchall())

for source, expected in expected_sources.items():
    actual = source_counts.get(source, 0)
    print(f"{source}: {actual} (beklenen: {expected})")

# Tekrarlanan FQDN kontrolü
duplicate_fqdns = cursor.execute("""
    SELECT fqdn, COUNT(*)
    FROM dns_records
    GROUP BY fqdn
    HAVING COUNT(*) > 1
""").fetchall()

# Tekrarlanan IP kontrolü
duplicate_ips = cursor.execute("""
    SELECT ip_address, COUNT(*)
    FROM dns_records
    GROUP BY ip_address
    HAVING COUNT(*) > 1
""").fetchall()

# Eksik veya hatalı alan kontrolü
invalid_records = cursor.execute("""
    SELECT COUNT(*)
    FROM dns_records
    WHERE hostname IS NULL OR hostname = ''
       OR fqdn IS NULL OR fqdn = ''
       OR ip_address IS NULL OR ip_address = ''
       OR record_type != 'A'
       OR record_status != 'Active'
""").fetchone()[0]

expected_total = sum(expected_sources.values())

print("\nTekrarlanan FQDN:", len(duplicate_fqdns))
print("Tekrarlanan IP:", len(duplicate_ips))
print("Eksik veya hatalı kayıt:", invalid_records)

success = (
    total == expected_total
    and all(
        source_counts.get(source, 0) == count
        for source, count in expected_sources.items()
    )
    and not duplicate_fqdns
    and not duplicate_ips
    and invalid_records == 0
)

if success:
    print("\nSONUÇ: TÜM DNS KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

    if duplicate_fqdns:
        print("Tekrarlanan FQDN örnekleri:", duplicate_fqdns[:10])

    if duplicate_ips:
        print("Tekrarlanan IP örnekleri:", duplicate_ips[:10])

conn.close()
