
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(42)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM ad_login_events"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"Tabloda zaten {existing} kayıt var. İşlem durduruldu."
    )

# AD kullanıcılarını al
users = cursor.execute("""
    SELECT ad_user_id, account_status
    FROM ad_users
""").fetchall()

enabled_users = [
    user[0] for user in users if user[1] == "Enabled"
]

all_users = [user[0] for user in users]

# Aktif bilgisayarları al
computers = cursor.execute("""
    SELECT hostname, ip_address, site_id
    FROM computers
    WHERE device_status = 'Active'
      AND ip_address IS NOT NULL
""").fetchall()

if not enabled_users or not computers:
    raise ValueError("AD kullanıcıları veya bilgisayarlar bulunamadı.")

events = []

start_date = datetime(2026, 10, 26, 0, 0, 0)
end_date = datetime(2026, 11, 24, 23, 59, 59)

logon_types = ["Interactive", "Network", "RemoteInteractive"]

failure_reasons = [
    "Bad password",
    "Account disabled",
    "Unknown username",
    "Account restriction"
]

# 3600 başarılı giriş
for _ in range(3600):
    user_id = random.choice(enabled_users)
    hostname, ip, site = random.choice(computers)

    event_time = start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

    events.append((
        user_id,
        4624,
        "Success",
        event_time.strftime("%Y-%m-%d %H:%M:%S"),
        ip,
        hostname,
        site,
        random.choice(logon_types),
        None
    ))

# 400 başarısız giriş
for _ in range(400):
    user_id = random.choice(all_users)
    hostname, ip, site = random.choice(computers)

    event_time = start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

    events.append((
        user_id,
        4625,
        "Failure",
        event_time.strftime("%Y-%m-%d %H:%M:%S"),
        ip,
        hostname,
        site,
        random.choice(logon_types),
        random.choice(failure_reasons)
    ))

random.shuffle(events)

cursor.executemany("""
    INSERT INTO ad_login_events (
        ad_user_id,
        windows_event_id,
        event_type,
        event_time,
        source_ip,
        source_hostname,
        site_id,
        logon_type,
        failure_reason
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", events)

conn.commit()

print("Toplam login event:", len(events))

print("\nOlay dağılımı:")
for row in cursor.execute("""
    SELECT event_type, windows_event_id, COUNT(*)
    FROM ad_login_events
    GROUP BY event_type, windows_event_id
"""):
    print(row)

print("\nLokasyon dağılımı:")
for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM ad_login_events
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

conn.close()
