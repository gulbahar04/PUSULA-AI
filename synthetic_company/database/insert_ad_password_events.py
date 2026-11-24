
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(43)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM ad_password_events"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"Tabloda zaten {existing} kayıt var. İşlem durduruldu."
    )

users = cursor.execute("""
    SELECT ad_user_id
    FROM ad_users
    WHERE account_status = 'Enabled'
""").fetchall()

computers = cursor.execute("""
    SELECT hostname, site_id
    FROM computers
    WHERE device_status = 'Active'
""").fetchall()

if not users or not computers:
    raise ValueError("AD kullanıcıları veya bilgisayarlar bulunamadı.")

events = []

start_date = datetime(2026, 10, 26)
end_date = datetime(2026, 11, 24, 23, 59, 59)

# 150 başarılı parola değiştirme işlemi
for _ in range(150):
    user_id = random.choice(users)[0]
    hostname, site = random.choice(computers)

    event_time = start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

    events.append((
        user_id,
        user_id,
        4723,
        event_time.strftime("%Y-%m-%d %H:%M:%S"),
        hostname,
        site,
        "Success"
    ))

# 30 başarılı parola sıfırlama işlemi
for _ in range(30):
    target_user = random.choice(users)[0]
    actor_user = random.choice(users)[0]
    hostname, site = random.choice(computers)

    event_time = start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

    events.append((
        target_user,
        actor_user,
        4724,
        event_time.strftime("%Y-%m-%d %H:%M:%S"),
        hostname,
        site,
        "Success"
    ))

# 20 başarısız parola değiştirme / sıfırlama girişimi
for _ in range(20):
    target_user = random.choice(users)[0]
    actor_user = random.choice(users)[0]
    hostname, site = random.choice(computers)

    event_time = start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

    event_id = random.choice([4723, 4724])

    events.append((
        target_user,
        actor_user,
        event_id,
        event_time.strftime("%Y-%m-%d %H:%M:%S"),
        hostname,
        site,
        "Failure"
    ))

random.shuffle(events)

cursor.executemany("""
    INSERT INTO ad_password_events (
        ad_user_id,
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

print("Toplam parola olayı:", len(events))

print("\nOlay dağılımı:")
for row in cursor.execute("""
    SELECT windows_event_id, operation_status, COUNT(*)
    FROM ad_password_events
    GROUP BY windows_event_id, operation_status
    ORDER BY windows_event_id, operation_status
"""):
    print(row)

print("\nLokasyon dağılımı:")
for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM ad_password_events
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

conn.close()
