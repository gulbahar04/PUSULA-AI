
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(46)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

existing = cursor.execute(
    "SELECT COUNT(*) FROM m365_signin_events"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"Tabloda zaten {existing} kayıt var. İşlem durduruldu."
    )

# Aktif M365 hesaplarını ve çalışan lokasyonlarını al
accounts = cursor.execute("""
    SELECT m.m365_account_id, m.mfa_enabled, e.site_id
    FROM m365_accounts m
    JOIN employees e ON m.employee_id = e.employee_id
    WHERE m.account_status = 'Active'
""").fetchall()

# Lokasyonlara göre aktif bilgisayarları al
computers_by_site = {}

for site, hostname, ip in cursor.execute("""
    SELECT site_id, hostname, ip_address
    FROM computers
    WHERE device_status = 'Active'
      AND ip_address IS NOT NULL
""").fetchall():
    computers_by_site.setdefault(site, []).append((hostname, ip))

if len(accounts) != 990:
    raise ValueError(
        f"990 aktif hesap bekleniyordu, bulunan: {len(accounts)}"
    )

if any(site not in computers_by_site for _, _, site in accounts):
    raise ValueError("Bazı lokasyonlarda aktif bilgisayar bulunamadı.")

mfa_accounts = [a for a in accounts if a[1] == 1]

events = []

start_date = datetime(2026, 10, 26)
end_date = datetime(2026, 11, 24, 23, 59, 59)

def random_time():
    return start_date + timedelta(
        seconds=random.randint(
            0, int((end_date - start_date).total_seconds())
        )
    )

def add_event(account, status, mfa_result, reason, risk):
    account_id, mfa_enabled, site = account
    hostname, ip = random.choice(computers_by_site[site])

    events.append((
        account_id,
        random_time().strftime("%Y-%m-%d %H:%M:%S"),
        "Interactive",
        status,
        ip,
        hostname,
        site,
        mfa_result,
        reason,
        risk
    ))

# 2700 başarılı giriş
for _ in range(2700):
    account = random.choice(accounts)

    mfa_result = "Success" if account[1] == 1 else "NotRequired"

    add_event(
        account,
        "Success",
        mfa_result,
        None,
        random.choices(
            ["None", "Low"],
            weights=[95, 5]
        )[0]
    )

# 240 başarısız parola girişimi
for _ in range(240):
    account = random.choice(accounts)

    mfa_result = "NotRequired" if account[1] == 0 else "NotApplicable"

    add_event(
        account,
        "Failure",
        mfa_result,
        "Invalid password",
        random.choices(
            ["Low", "Medium"],
            weights=[80, 20]
        )[0]
    )

# 60 başarısız MFA doğrulaması
for _ in range(60):
    account = random.choice(mfa_accounts)

    add_event(
        account,
        "Failure",
        "Failure",
        "MFA verification failed",
        random.choice(["Medium", "High"])
    )

random.shuffle(events)

cursor.executemany("""
    INSERT INTO m365_signin_events (
        m365_account_id,
        event_time,
        event_type,
        signin_status,
        source_ip,
        source_hostname,
        site_id,
        mfa_result,
        failure_reason,
        risk_level
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", events)

conn.commit()

print("Toplam M365 signin event:", len(events))

print("\nOturum dağılımı:")
for row in cursor.execute("""
    SELECT signin_status, COUNT(*)
    FROM m365_signin_events
    GROUP BY signin_status
"""):
    print(row)

print("\nMFA dağılımı:")
for row in cursor.execute("""
    SELECT mfa_result, COUNT(*)
    FROM m365_signin_events
    GROUP BY mfa_result
"""):
    print(row)

print("\nRisk dağılımı:")
for row in cursor.execute("""
    SELECT risk_level, COUNT(*)
    FROM m365_signin_events
    GROUP BY risk_level
"""):
    print(row)

conn.close()
