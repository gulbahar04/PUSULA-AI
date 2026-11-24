
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

total = cursor.execute("""
    SELECT COUNT(*) FROM ad_login_events
""").fetchone()[0]

# Event ID ve olay türü tutarlılığı
invalid_event_types = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_login_events
    WHERE NOT (
        (windows_event_id = 4624 AND event_type = 'Success')
        OR
        (windows_event_id = 4625 AND event_type = 'Failure')
    )
""").fetchone()[0]

# AD kullanıcısı bulunmayan kayıtlar
invalid_users = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_login_events e
    LEFT JOIN ad_users u ON e.ad_user_id = u.ad_user_id
    WHERE u.ad_user_id IS NULL
""").fetchone()[0]

# Bilgisayar-IP-hostname eşleşmesi
invalid_devices = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_login_events e
    LEFT JOIN computers c
      ON e.source_hostname = c.hostname
     AND e.source_ip = c.ip_address
     AND e.site_id = c.site_id
    WHERE c.computer_id IS NULL
""").fetchone()[0]

# Lokasyon eşleşmesi
invalid_sites = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_login_events e
    LEFT JOIN locations l ON e.site_id = l.site_id
    WHERE l.site_id IS NULL
""").fetchone()[0]

# Eksik zorunlu alanlar
missing_fields = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_login_events
    WHERE ad_user_id IS NULL
       OR event_time IS NULL
       OR source_ip IS NULL
       OR source_hostname IS NULL
       OR site_id IS NULL
""").fetchone()[0]

print("Toplam login event:", total)
print("Hatalı Event ID / olay türü:", invalid_event_types)
print("Geçersiz AD kullanıcısı:", invalid_users)
print("Geçersiz cihaz eşleşmesi:", invalid_devices)
print("Geçersiz lokasyon:", invalid_sites)
print("Eksik zorunlu alan:", missing_fields)

success = (
    total == 4000
    and invalid_event_types == 0
    and invalid_users == 0
    and invalid_devices == 0
    and invalid_sites == 0
    and missing_fields == 0
)

if success:
    print("\nSONUÇ: TÜM LOGIN EVENT KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

conn.close()
