
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(46)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    existing = cursor.execute(
        "SELECT COUNT(*) FROM server_events"
    ).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Tabloda zaten {existing} kayıt var. Tekrar ekleme yapılmadı."
        )

    servers = cursor.execute("""
        SELECT server_id, hostname, server_role, criticality
        FROM servers
        WHERE server_status = 'Active'
    """).fetchall()

    if not servers:
        raise RuntimeError("Aktif sunucu bulunamadı.")

    event_definitions = [
        ("HighCPU", "High", "CPU Usage", 85, 99,
         "Sunucu CPU kullanımı kritik seviyeye yaklaştı."),
        ("HighMemory", "High", "Memory Usage", 85, 99,
         "Sunucu bellek kullanımı yüksek seviyeye ulaştı."),
        ("LowDiskSpace", "Critical", "Disk Usage", 90, 99,
         "Sunucu disk alanı kritik seviyeye düştü."),
        ("ServiceDown", "Critical", "Service Status", None, None,
         "Sunucu üzerinde çalışan servis durdu."),
        ("ServiceRecovered", "Info", "Service Status", None, None,
         "Daha önce duran servis yeniden çalışmaya başladı."),
        ("BackupFailed", "High", "Backup Status", None, None,
         "Planlanan sunucu yedekleme işlemi başarısız oldu."),
        ("BackupCompleted", "Info", "Backup Status", None, None,
         "Sunucu yedekleme işlemi başarıyla tamamlandı."),
        ("ServerDown", "Critical", "Server Status", None, None,
         "Sunucu erişilemez duruma geldi."),
        ("ServerRestart", "Medium", "Server Status", None, None,
         "Sunucu yeniden başlatıldı."),
        ("SecurityAlert", "High", "Security", None, None,
         "Sunucuda güvenlik uyarısı tespit edildi."),
        ("UpdateFailed", "Medium", "Update Status", None, None,
         "Sunucu güncelleme işlemi başarısız oldu.")
    ]

    now = datetime(2026, 11, 24, 20, 0, 0)
    start = now - timedelta(days=29)

    rows = []

    for _ in range(1000):
        server_id, hostname, server_role, criticality = random.choice(servers)

        event_type, severity, metric, min_value, max_value, description = (
            random.choice(event_definitions)
        )

        metric_value = None
        if min_value is not None:
            metric_value = round(
                random.uniform(min_value, max_value), 2
            )

        event_time = start + timedelta(
            seconds=random.randint(
                0, int((now - start).total_seconds())
            )
        )

        rows.append((
            event_time.strftime("%Y-%m-%d %H:%M:%S"),
            server_id,
            event_type,
            severity,
            metric,
            metric_value,
            f"{hostname}: {description}"
        ))

    cursor.executemany("""
        INSERT INTO server_events (
            event_time, server_id, event_type,
            severity, metric_name, metric_value, description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()

    print(f"Eklenen sunucu olayı: {len(rows)}")

    print("\nOlay türü dağılımı:")
    for row in cursor.execute("""
        SELECT event_type, COUNT(*)
        FROM server_events
        GROUP BY event_type
        ORDER BY event_type
    """):
        print(row)

    print("\nÖnem derecesi dağılımı:")
    for row in cursor.execute("""
        SELECT severity, COUNT(*)
        FROM server_events
        GROUP BY severity
    """):
        print(row)

    print("\nSunucu olayları başarıyla eklendi.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
