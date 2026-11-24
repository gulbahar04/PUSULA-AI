
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(43)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    existing = cursor.execute(
        "SELECT COUNT(*) FROM network_events"
    ).fetchone()[0]

    if existing > 0:
        raise RuntimeError(
            f"Tabloda zaten {existing} kayıt var. Tekrar ekleme yapılmadı."
        )

    devices = cursor.execute("""
        SELECT device_id, hostname, device_type, site_id
        FROM network_devices
        WHERE device_status = 'Active'
    """).fetchall()

    if not devices:
        raise RuntimeError("Aktif ağ cihazı bulunamadı.")

    event_definitions = {
        "Switch": [
            ("PortDown", "High", "GigabitEthernet0/1", "Switch port bağlantısı kesildi"),
            ("PortUp", "Info", "GigabitEthernet0/1", "Switch port bağlantısı yeniden kuruldu"),
            ("PacketLoss", "Medium", "GigabitEthernet0/2", "Switch üzerinde paket kaybı tespit edildi"),
            ("HighLatency", "Medium", "GigabitEthernet0/3", "Switch portunda yüksek gecikme tespit edildi"),
            ("InterfaceError", "High", "GigabitEthernet0/4", "Switch arayüzünde hata oluştu"),
            ("DeviceRestart", "Medium", None, "Switch yeniden başlatıldı"),
        ],
        "Router": [
            ("DeviceDown", "Critical", None, "Router erişilemez duruma geldi"),
            ("DeviceUp", "Info", None, "Router bağlantısı yeniden kuruldu"),
            ("HighLatency", "High", "WAN", "Router WAN bağlantısında yüksek gecikme"),
            ("PacketLoss", "High", "WAN", "Router WAN bağlantısında paket kaybı"),
            ("DeviceRestart", "Medium", None, "Router yeniden başlatıldı"),
        ],
        "Firewall": [
            ("DeviceDown", "Critical", None, "Firewall erişilemez duruma geldi"),
            ("DeviceUp", "Info", None, "Firewall bağlantısı yeniden kuruldu"),
            ("HighLatency", "High", "WAN", "Firewall üzerinde yüksek gecikme"),
            ("InterfaceError", "High", "WAN", "Firewall arayüz hatası"),
            ("DeviceRestart", "Medium", None, "Firewall yeniden başlatıldı"),
        ],
        "Access Point": [
            ("DeviceDown", "High", None, "Access Point bağlantısı kesildi"),
            ("DeviceUp", "Info", None, "Access Point yeniden erişilebilir oldu"),
            ("PacketLoss", "Medium", "WLAN", "Kablosuz ağda paket kaybı"),
            ("HighLatency", "Medium", "WLAN", "Kablosuz ağda yüksek gecikme"),
            ("DeviceRestart", "Low", None, "Access Point yeniden başlatıldı"),
        ],
    }

    now = datetime(2026, 11, 24, 20, 0, 0)
    start = now - timedelta(days=29)

    rows = []

    for _ in range(500):
        device_id, hostname, device_type, site_id = random.choice(devices)

        event_type, severity, interface, description = random.choice(
            event_definitions[device_type]
        )

        event_time = start + timedelta(
            seconds=random.randint(
                0, int((now - start).total_seconds())
            )
        )

        duration = None
        if event_type in (
            "DeviceDown", "PortDown", "HighLatency", "PacketLoss",
            "InterfaceError"
        ):
            duration = random.randint(10, 3600)

        rows.append((
            event_time.strftime("%Y-%m-%d %H:%M:%S"),
            device_id,
            site_id,
            event_type,
            severity,
            interface,
            f"{hostname}: {description}",
            duration
        ))

    cursor.executemany("""
        INSERT INTO network_events (
            event_time, device_id, site_id, event_type,
            severity, interface_name, description, duration_seconds
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()

    print(f"Eklenen network olayı: {len(rows)}")

    print("\nOlay türleri:")
    for row in cursor.execute("""
        SELECT event_type, COUNT(*)
        FROM network_events
        GROUP BY event_type
        ORDER BY event_type
    """):
        print(row)

    print("\nLokasyon dağılımı:")
    for row in cursor.execute("""
        SELECT site_id, COUNT(*)
        FROM network_events
        GROUP BY site_id
    """):
        print(row)

    print("\nNetwork kayıtları başarıyla eklendi.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
