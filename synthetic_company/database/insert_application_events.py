
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(47)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    existing = cursor.execute(
        "SELECT COUNT(*) FROM application_events"
    ).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Tabloda zaten {existing} kayıt var. Tekrar ekleme yapılmadı."
        )

    applications = cursor.execute("""
        SELECT id, application_name, server_id
        FROM application_servers
    """).fetchall()

    if not applications:
        raise RuntimeError("Uygulama sunucusu bulunamadı.")

    event_definitions = [
        ("ApplicationDown", "Critical", None, "APP-503",
         "Uygulama hizmeti erişilemez duruma geldi."),
        ("ApplicationRecovered", "Info", None, None,
         "Uygulama hizmeti yeniden erişilebilir oldu."),
        ("DatabaseConnectionError", "High", None, "DB-1001",
         "Uygulama veritabanına bağlantı kuramadı."),
        ("HighResponseTime", "Medium", 3000, "PERF-001",
         "Uygulamanın yanıt süresi normal seviyenin üzerine çıktı."),
        ("AuthenticationFailure", "Medium", None, "AUTH-401",
         "Uygulama kimlik doğrulama işlemi başarısız oldu."),
        ("ApplicationError", "High", None, "APP-500",
         "Uygulama çalışma sırasında beklenmeyen hata verdi."),
        ("ServiceUnavailable", "Critical", None, "APP-503",
         "Uygulama servisi geçici olarak kullanılamıyor.")
    ]

    now = datetime(2026, 11, 24, 20, 0, 0)
    start = now - timedelta(days=29)

    rows = []

    for _ in range(1000):
        app_id, app_name, server_id = random.choice(applications)

        event_type, severity, response_time, error_code, description = (
            random.choice(event_definitions)
        )

        if event_type == "HighResponseTime":
            response_time = random.randint(3000, 10000)
        elif random.random() < 0.15:
            response_time = random.randint(100, 2500)

        event_time = start + timedelta(
            seconds=random.randint(
                0, int((now - start).total_seconds())
            )
        )

        rows.append((
            event_time.strftime("%Y-%m-%d %H:%M:%S"),
            app_id,
            event_type,
            severity,
            response_time,
            error_code,
            f"{app_name}: {description}"
        ))

    cursor.executemany("""
        INSERT INTO application_events (
            event_time,
            application_server_id,
            event_type,
            severity,
            response_time_ms,
            error_code,
            description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()

    print(f"Eklenen uygulama olayı: {len(rows)}")

    print("\nOlay türü dağılımı:")
    for row in cursor.execute("""
        SELECT event_type, COUNT(*)
        FROM application_events
        GROUP BY event_type
        ORDER BY event_type
    """):
        print(row)

    print("\nÖnem derecesi dağılımı:")
    for row in cursor.execute("""
        SELECT severity, COUNT(*)
        FROM application_events
        GROUP BY severity
    """):
        print(row)

    print("\nUygulama dağılımı:")
    for row in cursor.execute("""
        SELECT a.application_name, COUNT(*)
        FROM application_events e
        JOIN application_servers a
          ON e.application_server_id = a.id
        GROUP BY a.application_name
    """):
        print(row)

    print("\nUygulama olayları başarıyla eklendi.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
