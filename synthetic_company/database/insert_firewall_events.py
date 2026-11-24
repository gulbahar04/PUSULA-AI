
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(42)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    existing = cursor.execute(
        "SELECT COUNT(*) FROM firewall_events"
    ).fetchone()[0]

    if existing > 0:
        raise RuntimeError(
            f"firewall_events tablosunda zaten {existing} kayıt var. "
            "Tekrar ekleme yapılmadı."
        )

    firewalls = {
        site: hostname
        for hostname, site in cursor.execute(
            """
            SELECT hostname, site_id
            FROM network_devices
            WHERE device_type = 'Firewall'
            """
        ).fetchall()
    }

    devices = cursor.execute(
        """
        SELECT ia.ip_address, ia.vlan_id, c.site_id, c.hostname
        FROM ip_assignments ia
        JOIN computers c ON c.computer_id = ia.computer_id
        WHERE ia.is_current = 1
        """
    ).fetchall()

    if not firewalls or not devices:
        raise RuntimeError("Firewall veya güncel cihaz IP kaydı bulunamadı.")

    devices_by_site = {}
    for device in devices:
        devices_by_site.setdefault(device[2], []).append(device)

    if not all(site in devices_by_site for site in firewalls):
        raise RuntimeError("Her lokasyon için güncel cihaz IP'si bulunamadı.")

    now = datetime(2026, 11, 24, 20, 0, 0)
    start = now - timedelta(days=29)

    rows = []

    for i in range(1500):
        site = random.choice(list(firewalls.keys()))
        firewall = firewalls[site]
        local_devices = devices_by_site[site]

        direction = random.choices(
            ["Outbound", "Inbound", "InterVLAN", "VPN"],
            weights=[55, 15, 20, 10]
        )[0]

        source = random.choice(local_devices)
        destination = random.choice(local_devices)

        while destination[0] == source[0]:
            destination = random.choice(local_devices)

        source_ip = source[0]
        destination_ip = destination[0]
        source_vlan = source[1]
        destination_vlan = destination[1]

        if direction == "Outbound":
            destination_ip = f"198.51.100.{random.randint(1, 254)}"
            destination_vlan = None
            source_zone = "CORPORATE"
            destination_zone = "INTERNET"

        elif direction == "Inbound":
            source_ip = f"203.0.113.{random.randint(1, 254)}"
            source_vlan = None
            source_zone = "INTERNET"
            destination_zone = "CORPORATE"

        elif direction == "InterVLAN":
            other_sites = [
                d for d in local_devices
                if d[1] != source_vlan
            ]
            if other_sites:
                destination = random.choice(other_sites)
                destination_ip = destination[0]
                destination_vlan = destination[1]
            source_zone = f"VLAN_{source_vlan}"
            destination_zone = f"VLAN_{destination_vlan}"

        else:
            source_ip = f"198.51.100.{random.randint(1, 254)}"
            source_vlan = None
            source_zone = "VPN"
            destination_zone = "CORPORATE"

        protocol = random.choices(
            ["TCP", "UDP", "ICMP"],
            weights=[75, 20, 5]
        )[0]

        destination_port = random.choice(
            [53, 80, 443, 445, 3389, 1433, 22, 25, 587]
        ) if protocol in ("TCP", "UDP") else None

        source_port = random.randint(1024, 65535) if protocol in ("TCP", "UDP") else None

        action = random.choices(
            ["Allow", "Deny"],
            weights=[80, 20]
        )[0]

        if direction == "VPN":
            event_type = "VPN"
            rule_name = "VPN_ACCESS_POLICY"
        elif action == "Deny":
            event_type = random.choices(
                ["Connection", "Threat"], weights=[65, 35]
            )[0]
            rule_name = random.choice([
                "DEFAULT_DENY",
                "BLOCK_UNAUTHORIZED_ACCESS",
                "BLOCK_SUSPICIOUS_TRAFFIC"
            ])
        else:
            event_type = "Connection"
            rule_name = random.choice([
                "ALLOW_CORPORATE_TRAFFIC",
                "ALLOW_ERP_ACCESS",
                "ALLOW_DNS",
                "ALLOW_WEB_TRAFFIC",
                "ALLOW_INTERVLAN"
            ])

        if action == "Deny":
            severity = random.choice(["Low", "Medium", "High"])
        else:
            severity = random.choices(
                ["Info", "Low"], weights=[85, 15]
            )[0]

        event_time = start + timedelta(
            seconds=random.randint(0, int((now - start).total_seconds()))
        )

        rows.append((
            event_time.strftime("%Y-%m-%d %H:%M:%S"),
            firewall,
            site,
            source_ip,
            destination_ip,
            source_port,
            destination_port,
            protocol,
            direction,
            source_zone,
            destination_zone,
            action,
            rule_name,
            event_type,
            severity
        ))

    cursor.executemany(
        """
        INSERT INTO firewall_events (
            event_time, firewall_hostname, site_id,
            source_ip, destination_ip, source_port,
            destination_port, protocol, direction,
            source_zone, destination_zone, action,
            rule_name, event_type, severity
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows
    )

    conn.commit()

    print(f"Eklenen firewall olayı: {len(rows)}")
    print("\nAction dağılımı:")
    for row in cursor.execute(
        "SELECT action, COUNT(*) FROM firewall_events GROUP BY action"
    ):
        print(row)

    print("\nLokasyon dağılımı:")
    for row in cursor.execute(
        "SELECT site_id, COUNT(*) FROM firewall_events GROUP BY site_id"
    ):
        print(row)

    print("\nFirewall kayıtları başarıyla eklendi.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
