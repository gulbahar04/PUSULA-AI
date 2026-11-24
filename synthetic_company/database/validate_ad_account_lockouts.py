
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
cursor = conn.cursor()

total = cursor.execute("""
    SELECT COUNT(*) FROM ad_account_lockouts
""").fetchone()[0]

invalid_event_ids = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_lockouts
    WHERE windows_event_id != 4740
""").fetchone()[0]

invalid_users = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_lockouts l
    LEFT JOIN ad_users u ON l.ad_user_id = u.ad_user_id
    WHERE u.ad_user_id IS NULL
""").fetchone()[0]

invalid_devices = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_lockouts l
    LEFT JOIN computers c
      ON l.source_hostname = c.hostname
     AND l.source_ip = c.ip_address
     AND l.site_id = c.site_id
    WHERE c.computer_id IS NULL
""").fetchone()[0]

invalid_sites = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_account_lockouts l
    LEFT JOIN locations loc ON l.site_id = loc.site_id
    WHERE loc.site_id IS NULL
""").fetchone()[0]

print("Toplam kilitlenme:", total)
print("Hatalı Event ID:", invalid_event_ids)
print("Geçersiz AD kullanıcısı:", invalid_users)
print("Geçersiz cihaz eşleşmesi:", invalid_devices)
print("Geçersiz lokasyon:", invalid_sites)

if (
    total == 80
    and invalid_event_ids == 0
    and invalid_users == 0
    and invalid_devices == 0
    and invalid_sites == 0
):
    print("\nSONUÇ: TÜM KİLİTLENME KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

conn.close()
