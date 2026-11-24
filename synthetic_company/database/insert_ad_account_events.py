
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(44)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM ad_account_events"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"Tabloda zaten {existing} kayıt var. İşlem durduruldu."
    )

enabled_users = cursor.execute("""
    SELECT ad_user_id
    FROM ad_users
    WHERE account_status = 'Enabled'
""").fetchall()

disabled_users = cursor.execute("""
    SELECT ad_user_id
    FROM ad_users
    WHERE account_status = 'Disabled'
""").fetchall()

computers = cursor.execute("""
    SELECT hostname, site_id
    FROM computers
    WHERE device_status = 'Active'
""").fetchall()

if not enabled_users or not disabled_users or not computers:
    raise ValueError("Gerekli kullanıcı veya bilgisayar verileri bulunamadı.")

events = []

start_date = datetime(2026, 10, 26)
end_date = datetime(2026, 11, 24, 23, 59, 59)

def random_time():
    return start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

# 50 kullanıcı hesabı oluşturma (4720)
for _ in range(50):
    target = random.choice(enabled_users)[0]
    actor = random.choice(enabled_users)[0]
    hostname, site = random.choice(computers)

    events.append((
        target, actor, 4720,
        random_time().strftime("%Y-%m-%d %H:%M:%S"),
        hostname, site, "Success"
    ))

# 15 kullanıcı hesabı etkinleştirme (4722)
for _ in range(15):
    target = random.choice(enabled_users)[0]
    actor = random.choice(enabled_users)[0]
    hostname, site = random.choice(computers)

    events.append((
        target, actor, 4722,
        random_time().strftime("%Y-%m-%d %H:%M:%S"),
        hostname, site, "Success"
    ))

# 30 kullanıcı hesabı devre dışı bırakma (4725)
for target_row in disabled_users:
    target = target_row[0]
    actor = random.choice(enabled_users)[0]
    hostname, site = random.choice(computers)

    events.append((
        target, actor, 4725,
        random_time().strftime("%Y-%m-%d %H:%M:%S"),
        hostname, site, "Success"
    ))

random.shuffle(events)

cursor.executemany("""
    INSERT INTO ad_account_events (
        target_ad_user_id,
        actor_ad_user_id,
        windows_event_id,
        event_time,
        source_hostname,
        site_id,
        operation_status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", events)

conn.commit()

print("Toplam hesap olayı:", len(events))

print("\nOlay dağılımı:")
for row in cursor.execute("""
    SELECT windows_event_id, operation_status, COUNT(*)
    FROM ad_account_events
    GROUP BY windows_event_id, operation_status
    ORDER BY windows_event_id
"""):
    print(row)

print("\nLokasyon dağılımı:")
for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM ad_account_events
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

conn.close()
