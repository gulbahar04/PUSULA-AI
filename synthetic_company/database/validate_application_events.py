
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

total = cursor.execute(
    "SELECT COUNT(*) FROM application_events"
).fetchone()[0]

invalid_application = cursor.execute("""
    SELECT COUNT(*)
    FROM application_events e
    LEFT JOIN application_servers a
      ON e.application_server_id = a.id
    WHERE a.id IS NULL
""").fetchone()[0]

invalid_server = cursor.execute("""
    SELECT COUNT(*)
    FROM application_events e
    JOIN application_servers a
      ON e.application_server_id = a.id
    LEFT JOIN servers s ON a.server_id = s.server_id
    WHERE s.server_id IS NULL
""").fetchone()[0]

invalid_response = cursor.execute("""
    SELECT COUNT(*)
    FROM application_events
    WHERE response_time_ms < 0
""").fetchone()[0]

missing_description = cursor.execute("""
    SELECT COUNT(*)
    FROM application_events
    WHERE description IS NULL OR TRIM(description) = ''
""").fetchone()[0]

invalid_dates = cursor.execute("""
    SELECT COUNT(*)
    FROM application_events
    WHERE event_time < '2026-10-26 00:00:00'
       OR event_time > '2026-11-24 20:00:00'
""").fetchone()[0]

checks = {
    "Toplam olay": total == 1000,
    "Geçersiz uygulama": invalid_application == 0,
    "Geçersiz sunucu ilişkisi": invalid_server == 0,
    "Geçersiz yanıt süresi": invalid_response == 0,
    "Eksik açıklama": missing_description == 0,
    "Geçersiz tarih": invalid_dates == 0
}

print(f"Toplam uygulama olayı: {total}")
print(f"Geçersiz uygulama: {invalid_application}")
print(f"Geçersiz sunucu ilişkisi: {invalid_server}")
print(f"Geçersiz yanıt süresi: {invalid_response}")
print(f"Eksik açıklama: {missing_description}")
print(f"Geçersiz tarih: {invalid_dates}")

print("\nSONUÇ:")
if all(checks.values()):
    print("TÜM APPLICATION EVENT KONTROLLERİ BAŞARILI.")
else:
    print("BAZI KONTROLLER BAŞARISIZ.")

conn.close()
