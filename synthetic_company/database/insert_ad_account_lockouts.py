
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(42)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM ad_account_lockouts"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"Tabloda zaten {existing} kayıt var. İşlem durduruldu."
    )

# Etkin AD hesaplarını al
users = cursor.execute("""
    SELECT ad_user_id
    FROM ad_users
    WHERE account_status = 'Enabled'
""").fetchall()

# Kilitlenmelerde kullanılacak bilgisayarlar
computers = cursor.execute("""
    SELECT hostname, ip_address, site_id
    FROM computers
    WHERE device_status = 'Active'
      AND ip_address IS NOT NULL
""").fetchall()

if len(users) == 0 or len(computers) == 0:
    raise ValueError("AD kullanıcıları veya bilgisayarlar bulunamadı.")

events = []

start_date = datetime(2026, 10, 26)
end_date = datetime(2026, 11, 24, 23, 59, 59)

# 80 sentetik hesap kilitlenmesi
for _ in range(80):
    user_id = random.choice(users)[0]
    hostname, ip, site = random.choice(computers)

    event_time = start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

    events.append((
        user_id,
        event_time.strftime("%Y-%m-%d %H:%M:%S"),
        hostname,
        ip,
        site,
        4740
    ))

cursor.executemany("""
    INSERT INTO ad_account_lockouts (
        ad_user_id,
        event_time,
        source_hostname,
        source_ip,
        site_id,
        windows_event_id
    )
    VALUES (?, ?, ?, ?, ?, ?)
""", events)

conn.commit()

print("Toplam hesap kilitlenmesi:", len(events))

print("\nLokasyon dağılımı:")
for row in cursor.execute("""
    SELECT site_id, COUNT(*)
    FROM ad_account_lockouts
    GROUP BY site_id
    ORDER BY site_id
"""):
    print(row)

conn.close()
