
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
cursor = conn.cursor()

total = cursor.execute("""
    SELECT COUNT(*) FROM ad_group_membership_events
""").fetchone()[0]

invalid_events = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_group_membership_events e
    JOIN ad_groups g ON e.group_id = g.group_id
    WHERE NOT (
        (g.group_name LIKE 'GG-%' OR g.group_name = 'Domain Admins')
        AND e.windows_event_id = 4728
        OR
        g.group_name LIKE 'DL-%'
        AND e.windows_event_id = 4732
    )
""").fetchone()[0]

invalid_users = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_group_membership_events e
    LEFT JOIN ad_users u ON e.target_ad_user_id = u.ad_user_id
    WHERE u.ad_user_id IS NULL
""").fetchone()[0]

invalid_actors = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_group_membership_events e
    LEFT JOIN ad_users u ON e.actor_ad_user_id = u.ad_user_id
    WHERE u.ad_user_id IS NULL OR u.is_privileged != 1
""").fetchone()[0]

invalid_memberships = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_group_membership_events e
    LEFT JOIN group_memberships gm
      ON e.target_ad_user_id = gm.ad_user_id
     AND e.group_id = gm.group_id
    WHERE gm.membership_id IS NULL
""").fetchone()[0]

invalid_sites = cursor.execute("""
    SELECT COUNT(*)
    FROM ad_group_membership_events e
    LEFT JOIN locations l ON e.site_id = l.site_id
    WHERE l.site_id IS NULL
""").fetchone()[0]

print("Toplam grup değişikliği:", total)
print("Hatalı Event ID / grup türü:", invalid_events)
print("Geçersiz hedef kullanıcı:", invalid_users)
print("Yetkisiz işlem yapan kullanıcı:", invalid_actors)
print("Mevcut üyelikle eşleşmeyen olay:", invalid_memberships)
print("Geçersiz lokasyon:", invalid_sites)

if (
    total == 5
    and invalid_events == 0
    and invalid_users == 0
    and invalid_actors == 0
    and invalid_memberships == 0
    and invalid_sites == 0
):
    print("\nSONUÇ: TÜM GRUP DEĞİŞİKLİĞİ KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

conn.close()
