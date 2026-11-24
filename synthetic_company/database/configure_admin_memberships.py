
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

admin_assignments = {
    "AD0001": ["G011", "G017", "G018"],
    "AD0002": ["G012", "G013"],
}

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    for ad_user_id, group_ids in admin_assignments.items():
        user = cursor.execute("""
            SELECT account_status
            FROM ad_users
            WHERE ad_user_id = ?
        """, (ad_user_id,)).fetchone()

        if not user:
            raise ValueError(f"{ad_user_id} bulunamadı.")

        if user[0] != "Enabled":
            raise ValueError(f"{ad_user_id} etkin değil.")

        cursor.execute("""
            UPDATE ad_users
            SET is_privileged = 1
            WHERE ad_user_id = ?
        """, (ad_user_id,))

        for group_id in group_ids:
            group = cursor.execute("""
                SELECT is_privileged
                FROM ad_groups
                WHERE group_id = ?
            """, (group_id,)).fetchone()

            if not group or group[0] != 1:
                raise ValueError(
                    f"{group_id} bulunamadı veya ayrıcalıklı grup değil."
                )

            cursor.execute("""
                INSERT INTO group_memberships (
                    ad_user_id, group_id, membership_date
                )
                SELECT ?, ?, DATE('now')
                WHERE NOT EXISTS (
                    SELECT 1 FROM group_memberships
                    WHERE ad_user_id = ? AND group_id = ?
                )
            """, (ad_user_id, group_id, ad_user_id, group_id))

    conn.commit()

    print("Ayrıcalıklı hesaplar güncellendi.")

    print("\nYönetici hesapları:")
    for row in cursor.execute("""
        SELECT ad_user_id, username, is_privileged
        FROM ad_users
        WHERE ad_user_id IN ('AD0001', 'AD0002')
    """):
        print(row)

    print("\nYönetici grup üyelikleri:")
    for row in cursor.execute("""
        SELECT u.ad_user_id, g.group_name
        FROM group_memberships gm
        JOIN ad_users u ON gm.ad_user_id = u.ad_user_id
        JOIN ad_groups g ON gm.group_id = g.group_id
        WHERE u.ad_user_id IN ('AD0001', 'AD0002')
        ORDER BY u.ad_user_id, g.group_id
    """):
        print(row)

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
