
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
cursor = conn.cursor()

expected = {
    "AD0001": {"G011", "G017", "G018"},
    "AD0002": {"G012", "G013"}
}

errors = []

for user_id, expected_groups in expected.items():
    user = cursor.execute("""
        SELECT is_privileged
        FROM ad_users
        WHERE ad_user_id = ?
    """, (user_id,)).fetchone()

    actual_groups = {
        row[0] for row in cursor.execute("""
            SELECT group_id
            FROM group_memberships
            WHERE ad_user_id = ?
        """, (user_id,))
    }

    if not user or user[0] != 1:
        errors.append(f"{user_id}: ayrıcalık durumu hatalı.")

    if not expected_groups.issubset(actual_groups):
        errors.append(f"{user_id}: grup üyelikleri eksik.")

# Ayrıcalıklı grup üyeliklerini say
privileged_memberships = cursor.execute("""
    SELECT COUNT(*)
    FROM group_memberships gm
    JOIN ad_groups g ON gm.group_id = g.group_id
    WHERE g.is_privileged = 1
""").fetchone()[0]

print("Yeni ayrıcalıklı grup üyeliği:", privileged_memberships)

if not errors:
    print("SONUÇ: YÖNETİCİ ÜYELİK KONTROLLERİ BAŞARILI.")
else:
    for error in errors:
        print(error)
    print("SONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

conn.close()
