
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(45)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM ad_group_membership_events"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"Tabloda zaten {existing} kayıt var. İşlem durduruldu."
    )

# Yalnızca yeni eklediğimiz 5 ayrıcalıklı üyeliği al
memberships = cursor.execute("""
    SELECT
        gm.ad_user_id,
        gm.group_id,
        gm.membership_date,
        g.group_name
    FROM group_memberships gm
    JOIN ad_groups g ON gm.group_id = g.group_id
    WHERE gm.ad_user_id IN ('AD0001', 'AD0002')
      AND g.is_privileged = 1
    ORDER BY gm.ad_user_id, gm.group_id
""").fetchall()

if len(memberships) != 5:
    raise ValueError(
        f"5 ayrıcalıklı üyelik bekleniyordu, bulunan: {len(memberships)}"
    )

events = []

# İki yönetici birbirlerinin üyelik işlemlerini gerçekleştiriyor
actors = {
    "AD0001": "AD0002",
    "AD0002": "AD0001"
}

for target_user, group_id, membership_date, group_name in memberships:

    actor_user = actors[target_user]

    # Global / Domain Local grup ayrımı
    if group_name.startswith("DL-"):
        event_id = 4732
    else:
        event_id = 4728

    actor_site = cursor.execute("""
        SELECT e.site_id
        FROM ad_users a
        JOIN employees e ON a.employee_id = e.employee_id
        WHERE a.ad_user_id = ?
    """, (actor_user,)).fetchone()

    if not actor_site:
        raise ValueError(f"{actor_user} için lokasyon bulunamadı.")

    site_id = actor_site[0]

    computer = cursor.execute("""
        SELECT hostname
        FROM computers
        WHERE site_id = ?
          AND device_status = 'Active'
        ORDER BY RANDOM()
        LIMIT 1
    """, (site_id,)).fetchone()

    if not computer:
        raise ValueError(f"{site_id} lokasyonunda bilgisayar bulunamadı.")

    event_date = datetime.strptime(
        membership_date, "%Y-%m-%d"
    ) + timedelta(
        hours=random.randint(8, 17),
        minutes=random.randint(0, 59)
    )

    events.append((
        target_user,
        group_id,
        actor_user,
        event_id,
        event_date.strftime("%Y-%m-%d %H:%M:%S"),
        computer[0],
        site_id,
        "Success"
    ))

cursor.executemany("""
    INSERT INTO ad_group_membership_events (
        target_ad_user_id,
        group_id,
        actor_ad_user_id,
        windows_event_id,
        event_time,
        source_hostname,
        site_id,
        operation_status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", events)

conn.commit()

print("Toplam grup değişikliği:", len(events))

print("\nOlay dağılımı:")
for row in cursor.execute("""
    SELECT windows_event_id, COUNT(*)
    FROM ad_group_membership_events
    GROUP BY windows_event_id
    ORDER BY windows_event_id
"""):
    print(row)

print("\nGrup değişiklikleri:")
for row in cursor.execute("""
    SELECT e.target_ad_user_id, g.group_name,
           e.actor_ad_user_id, e.windows_event_id
    FROM ad_group_membership_events e
    JOIN ad_groups g ON e.group_id = g.group_id
    ORDER BY e.target_ad_user_id, g.group_id
"""):
    print(row)

conn.close()
