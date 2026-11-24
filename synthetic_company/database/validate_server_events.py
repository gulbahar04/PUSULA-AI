
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

total = cursor.execute(
    "SELECT COUNT(*) FROM server_events"
).fetchone()[0]

invalid_servers = cursor.execute("""
    SELECT COUNT(*)
    FROM server_events e
    LEFT JOIN servers s ON e.server_id = s.server_id
    WHERE s.server_id IS NULL
       OR s.server_status != 'Active'
""").fetchone()[0]

invalid_metrics = cursor.execute("""
    SELECT COUNT(*)
    FROM server_events
    WHERE metric_value IS NOT NULL
      AND (
          metric_value < 0
          OR metric_value > 100
      )
""").fetchone()[0]

missing_descriptions = cursor.execute("""
    SELECT COUNT(*)
    FROM server_events
    WHERE description IS NULL OR TRIM(description) = ''
""").fetchone()[0]

invalid_dates = cursor.execute("""
    SELECT COUNT(*)
    FROM server_events
    WHERE event_time < '2026-10-26 00:00:00'
       OR event_time > '2026-11-24 20:00:00'
""").fetchone()[0]

checks = {
    "Toplam olay": total == 1000,
    "Geçersiz sunucu": invalid_servers == 0,
    "Geçersiz metrik": invalid_metrics == 0,
    "Eksik açıklama": missing_descriptions == 0,
    "Geçersiz tarih": invalid_dates == 0
}

print(f"Toplam sunucu olayı: {total}")
print(f"Geçersiz sunucu: {invalid_servers}")
print(f"Geçersiz metrik: {invalid_metrics}")
print(f"Eksik açıklama: {missing_descriptions}")
print(f"Geçersiz tarih: {invalid_dates}")

print("\nSONUÇ:")
if all(checks.values()):
    print("TÜM SERVER EVENT KONTROLLERİ BAŞARILI.")
else:
    print("BAZI KONTROLLER BAŞARISIZ.")

conn.close()
