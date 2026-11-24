
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
cursor = conn.cursor()

total = cursor.execute("""
    SELECT COUNT(*) FROM ad_password_events
""").fetchone()[0]

invalid_events = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_password_events
    WHERE windows_event_id NOT IN (4723, 4724)
       OR operation_status NOT IN ('Success', 'Failure')
""").fetchone()[0]

invalid_users = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_password_events e
    LEFT JOIN ad_users u ON e.ad_user_id = u.ad_user_id
    WHERE u.ad_user_id IS NULL
""").fetchone()[0]

invalid_actors = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_password_events e
    LEFT JOIN ad_users u ON e.actor_ad_user_id = u.ad_user_id
    WHERE e.actor_ad_user_id IS NOT NULL
      AND u.ad_user_id IS NULL
""").fetchone()[0]

invalid_sites = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_password_events e
    LEFT JOIN locations l ON e.site_id = l.site_id
    WHERE l.site_id IS NULL
""").fetchone()[0]

missing_fields = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_password_events
    WHERE ad_user_id IS NULL
       OR event_time IS NULL
       OR source_hostname IS NULL
       OR site_id IS NULL
       OR operation_status IS NULL
""").fetchone()[0]

print("Toplam parola olayı:", total)
print("Geçersiz Event ID / işlem durumu:", invalid_events)
print("Geçersiz hedef kullanıcı:", invalid_users)
print("Geçersiz işlemi yapan kullanıcı:", invalid_actors)
print("Geçersiz lokasyon:", invalid_sites)
print("Eksik alan:", missing_fields)

if (
    total == 200
    and invalid_events == 0
    and invalid_users == 0
    and invalid_actors == 0
    and invalid_sites == 0
    and missing_fields == 0
):
    print("\nSONUÇ: TÜM PAROLA OLAYI KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

conn.close()
