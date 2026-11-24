
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
cursor = conn.cursor()

total = cursor.execute("""
    SELECT COUNT(*) FROM ad_account_events
""").fetchone()[0]

invalid_events = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_events
    WHERE windows_event_id NOT IN (4720, 4722, 4725)
       OR operation_status != 'Success'
""").fetchone()[0]

invalid_targets = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_events e
    LEFT JOIN ad_users u
      ON e.target_ad_user_id = u.ad_user_id
    WHERE u.ad_user_id IS NULL
""").fetchone()[0]

invalid_actors = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_events e
    LEFT JOIN ad_users u
      ON e.actor_ad_user_id = u.ad_user_id
    WHERE e.actor_ad_user_id IS NOT NULL
      AND u.ad_user_id IS NULL
""").fetchone()[0]

invalid_sites = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_events e
    LEFT JOIN locations l ON e.site_id = l.site_id
    WHERE l.site_id IS NULL
""").fetchone()[0]

invalid_devices = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_events e
    LEFT JOIN computers c
      ON e.source_hostname = c.hostname
     AND e.site_id = c.site_id
    WHERE c.computer_id IS NULL
""").fetchone()[0]

print("Toplam hesap olayı:", total)
print("Hatalı Event ID / durum:", invalid_events)
print("Geçersiz hedef kullanıcı:", invalid_targets)
print("Geçersiz işlemi yapan kullanıcı:", invalid_actors)
print("Geçersiz lokasyon:", invalid_sites)
print("Geçersiz bilgisayar:", invalid_devices)

if (
    total == 95
    and invalid_events == 0
    and invalid_targets == 0
    and invalid_actors == 0
    and invalid_sites == 0
    and invalid_devices == 0
):
    print("\nSONUÇ: TÜM HESAP OLAYI KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

conn.close()
