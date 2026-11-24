
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

total = cursor.execute(
    "SELECT COUNT(*) FROM network_events"
).fetchone()[0]

invalid_devices = cursor.execute("""
    SELECT COUNT(*)
    FROM network_events e
    LEFT JOIN network_devices d ON e.device_id = d.device_id
    WHERE d.device_id IS NULL
       OR d.site_id != e.site_id
""").fetchone()[0]

invalid_sites = cursor.execute("""
    SELECT COUNT(*)
    FROM network_events e
    LEFT JOIN locations l ON e.site_id = l.site_id
    WHERE l.site_id IS NULL
""").fetchone()[0]

invalid_types = cursor.execute("""
    SELECT COUNT(*)
    FROM network_events
    WHERE event_type NOT IN (
        'DeviceDown', 'DeviceUp', 'PortDown', 'PortUp',
        'HighLatency', 'PacketLoss', 'DeviceRestart',
        'InterfaceError'
    )
""").fetchone()[0]

invalid_durations = cursor.execute("""
    SELECT COUNT(*)
    FROM network_events
    WHERE duration_seconds < 0
""").fetchone()[0]

checks = {
    "Toplam olay": total == 500,
    "Geçersiz cihaz/lokasyon eşleşmesi": invalid_devices == 0,
    "Geçersiz lokasyon": invalid_sites == 0,
    "Geçersiz olay türü": invalid_types == 0,
    "Geçersiz süre": invalid_durations == 0
}

print(f"Toplam network olayı: {total}")
print(f"Geçersiz cihaz/lokasyon eşleşmesi: {invalid_devices}")
print(f"Geçersiz lokasyon: {invalid_sites}")
print(f"Geçersiz olay türü: {invalid_types}")
print(f"Geçersiz süre: {invalid_durations}")

print("\nSONUÇ:")
if all(checks.values()):
    print("TÜM NETWORK KONTROLLERİ BAŞARILI.")
else:
    print("BAZI KONTROLLER BAŞARISIZ.")

conn.close()
