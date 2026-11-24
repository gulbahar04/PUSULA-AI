
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

errors = []

total = cursor.execute(
    "SELECT COUNT(*) FROM firewall_events"
).fetchone()[0]

invalid_firewall = cursor.execute("""
    SELECT COUNT(*)
    FROM firewall_events f
    LEFT JOIN network_devices n
      ON f.firewall_hostname = n.hostname
     AND f.site_id = n.site_id
     AND n.device_type = 'Firewall'
    WHERE n.hostname IS NULL
""").fetchone()[0]

invalid_site = cursor.execute("""
    SELECT COUNT(*)
    FROM firewall_events f
    LEFT JOIN locations l ON f.site_id = l.site_id
    WHERE l.site_id IS NULL
""").fetchone()[0]

invalid_direction = cursor.execute("""
    SELECT COUNT(*)
    FROM firewall_events
    WHERE
      (direction = 'Outbound'
       AND (source_zone != 'CORPORATE'
            OR destination_zone != 'INTERNET'))
      OR
      (direction = 'Inbound'
       AND (source_zone != 'INTERNET'
            OR destination_zone != 'CORPORATE'))
      OR
      (direction = 'VPN'
       AND (source_zone != 'VPN'
            OR destination_zone != 'CORPORATE'))
""").fetchone()[0]

invalid_ports = cursor.execute("""
    SELECT COUNT(*)
    FROM firewall_events
    WHERE (source_port IS NOT NULL
           AND source_port NOT BETWEEN 1 AND 65535)
       OR (destination_port IS NOT NULL
           AND destination_port NOT BETWEEN 1 AND 65535)
""").fetchone()[0]

invalid_action = cursor.execute("""
    SELECT COUNT(*)
    FROM firewall_events
    WHERE action NOT IN ('Allow', 'Deny')
""").fetchone()[0]

checks = {
    "Toplam olay": total == 1500,
    "Geçersiz firewall cihazı": invalid_firewall == 0,
    "Geçersiz lokasyon": invalid_site == 0,
    "Yön ve zone tutarsızlığı": invalid_direction == 0,
    "Geçersiz port": invalid_ports == 0,
    "Geçersiz aksiyon": invalid_action == 0
}

print(f"Toplam firewall olayı: {total}")
print(f"Geçersiz firewall cihazı: {invalid_firewall}")
print(f"Geçersiz lokasyon: {invalid_site}")
print(f"Yön ve zone tutarsızlığı: {invalid_direction}")
print(f"Geçersiz port: {invalid_ports}")
print(f"Geçersiz aksiyon: {invalid_action}")

print("\nSONUÇ:")
if all(checks.values()):
    print("TÜM FIREWALL KONTROLLERİ BAŞARILI.")
else:
    print("BAZI KONTROLLER BAŞARISIZ.")

conn.close()
