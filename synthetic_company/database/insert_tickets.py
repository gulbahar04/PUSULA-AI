
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(44)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    existing = cursor.execute(
        "SELECT COUNT(*) FROM tickets"
    ).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"tickets tablosunda zaten {existing} kayıt var."
        )

    employees = cursor.execute("""
        SELECT employee_id, site_id
        FROM employees
        WHERE employment_status = 'Active'
    """).fetchall()

    it_support = cursor.execute("""
        SELECT a.ad_user_id
        FROM ad_users a
        JOIN employees e ON a.employee_id = e.employee_id
        WHERE e.dept_id = 'IT'
          AND a.account_status = 'Enabled'
    """).fetchall()

    assignments = cursor.execute("""
        SELECT computer_id, employee_id
        FROM computer_assignments
        WHERE assignment_status = 'Active'
    """).fetchall()

    if not employees or not it_support:
        raise RuntimeError("Aktif çalışan veya IT destek hesabı bulunamadı.")

    assignments_by_employee = {}
    for computer_id, employee_id in assignments:
        assignments_by_employee.setdefault(employee_id, []).append(
            computer_id
        )

    categories = {
        "Account Access": [
            ("Account Lockout", "Kullanıcı hesabı kilitlendi"),
            ("Password Reset", "Kullanıcı parola sıfırlama talebinde bulundu"),
            ("Permission", "Sistem erişim yetkisi talep edildi"),
        ],
        "Network": [
            ("VPN", "VPN bağlantısı kurulamıyor"),
            ("Connectivity", "Kurumsal ağa erişim sorunu"),
            ("Wi-Fi", "Kablosuz ağ bağlantısı kesiliyor"),
        ],
        "Hardware": [
            ("Laptop", "Bilgisayar performans ve donanım sorunu"),
            ("Monitor", "Monitör görüntü vermiyor"),
            ("Keyboard", "Klavye düzgün çalışmıyor"),
        ],
        "Software": [
            ("Installation", "Yazılım kurulumu talebi"),
            ("Application Error", "Uygulama beklenmedik şekilde kapanıyor"),
            ("Update", "Yazılım güncelleme sorunu"),
        ],
        "Email": [
            ("Outlook", "Outlook uygulamasında e-posta sorunu"),
            ("Mailbox", "Posta kutusuna erişilemiyor"),
        ],
        "Printer": [
            ("Print Error", "Yazıcıdan çıktı alınamıyor"),
            ("Printer Connection", "Yazıcı bağlantısı kurulamıyor"),
        ],
        "Server": [
            ("ERP", "ERP sunucusuna erişilemiyor"),
            ("File Server", "Dosya sunucusuna erişim sorunu"),
        ],
        "Other": [
            ("General Support", "Genel IT destek talebi"),
        ],
    }

    priorities = ["Low", "Medium", "High", "Critical"]
    priority_weights = [20, 50, 25, 5]

    statuses = ["Open", "In Progress", "Pending", "Resolved", "Closed"]
    status_weights = [10, 20, 10, 25, 35]

    now = datetime(2026, 11, 24, 20, 0, 0)
    start = now - timedelta(days=29)

    rows = []

    for i in range(1, 1001):
        employee_id, site_id = random.choice(employees)

        category = random.choice(list(categories.keys()))
        subcategory, description = random.choice(categories[category])

        priority = random.choices(
            priorities, weights=priority_weights
        )[0]

        status = random.choices(
            statuses, weights=status_weights
        )[0]

        created_at = start + timedelta(
            seconds=random.randint(
                0, int((now - start).total_seconds())
            )
        )

        updated_at = created_at + timedelta(
            seconds=random.randint(
                0, int((now - created_at).total_seconds())
            )
        )

        resolved_at = None
        if status in ("Resolved", "Closed"):
            resolved_at = updated_at
            if resolved_at <= created_at:
                resolved_at = created_at + timedelta(minutes=5)

        computer_options = assignments_by_employee.get(employee_id, [])
        related_computer_id = (
            random.choice(computer_options)
            if computer_options else None
        )

        assigned_ad_user_id = random.choice(it_support)[0]

        subject = f"{category} - {subcategory}"

        rows.append((
            f"TKT{i:04d}",
            employee_id,
            assigned_ad_user_id,
            category,
            subcategory,
            subject,
            description,
            priority,
            status,
            created_at.strftime("%Y-%m-%d %H:%M:%S"),
            updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            resolved_at.strftime("%Y-%m-%d %H:%M:%S")
                if resolved_at else None,
            site_id,
            related_computer_id
        ))

    cursor.executemany("""
        INSERT INTO tickets (
            ticket_id, employee_id, assigned_ad_user_id,
            category, subcategory, subject, description,
            priority, status, created_at, updated_at,
            resolved_at, site_id, related_computer_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    conn.commit()

    print(f"Eklenen destek talebi: {len(rows)}")

    print("\nDurum dağılımı:")
    for row in cursor.execute("""
        SELECT status, COUNT(*)
        FROM tickets GROUP BY status
    """):
        print(row)

    print("\nKategori dağılımı:")
    for row in cursor.execute("""
        SELECT category, COUNT(*)
        FROM tickets GROUP BY category
    """):
        print(row)

    print("\nLokasyon dağılımı:")
    for row in cursor.execute("""
        SELECT site_id, COUNT(*)
        FROM tickets GROUP BY site_id
    """):
        print(row)

    print("\nDestek talepleri başarıyla eklendi.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
