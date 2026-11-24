
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "synthetic_company/database/company.db"
random.seed(45)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

try:
    existing = cursor.execute(
        "SELECT COUNT(*) FROM ticket_comments"
    ).fetchone()[0]

    if existing:
        raise RuntimeError(
            f"Tabloda zaten {existing} yorum var. Tekrar ekleme yapılmadı."
        )

    tickets = cursor.execute("""
        SELECT
            ticket_id, employee_id, assigned_ad_user_id,
            category, subcategory, status,
            created_at, updated_at, resolved_at
        FROM tickets
    """).fetchall()

    rows = []

    for ticket in tickets:
        (
            ticket_id, employee_id, assigned_ad_user_id,
            category, subcategory, status,
            created_at, updated_at, resolved_at
        ) = ticket

        created = datetime.strptime(
            created_at, "%Y-%m-%d %H:%M:%S"
        )
        updated = datetime.strptime(
            updated_at, "%Y-%m-%d %H:%M:%S"
        )

        it_employee = cursor.execute("""
            SELECT employee_id
            FROM ad_users
            WHERE ad_user_id = ?
        """, (assigned_ad_user_id,)).fetchone()[0]

        # Kullanıcının ilk mesajı
        user_messages = {
            "Account Access": "Sorunla ilgili destek talebi oluşturdum. Hesabıma erişemiyorum.",
            "Network": "Kurumsal ağ bağlantısında sorun yaşıyorum. Kontrol edilmesini rica ederim.",
            "Hardware": "Bilgisayarımda donanımsal bir sorun yaşıyorum.",
            "Software": "Kullandığım yazılımda hata alıyorum. Yardım rica ederim.",
            "Email": "E-posta hesabımla ilgili sorun yaşıyorum.",
            "Printer": "Yazıcıya bağlanamıyorum veya çıktı alamıyorum.",
            "Server": "İlgili sunucuya erişim sağlayamıyorum.",
            "Other": "IT desteğine ihtiyaç duyuyorum. Konunun incelenmesini rica ederim."
        }

        rows.append((
            ticket_id,
            employee_id,
            user_messages[category],
            "UserMessage",
            created.strftime("%Y-%m-%d %H:%M:%S")
        ))

        # IT yanıtı
        it_responses = [
            "Talebiniz incelenmeye alınmıştır. Gerekli kontroller yapılıyor.",
            "İlgili sistem ve kullanıcı kayıtları kontrol ediliyor.",
            "Sorunun kaynağını belirlemek için teknik inceleme başlatıldı.",
            "İlgili cihaz ve erişim ayarları kontrol edildi."
        ]

        response_time = created + (updated - created) / 2

        rows.append((
            ticket_id,
            it_employee,
            random.choice(it_responses),
            "ITResponse",
            response_time.strftime("%Y-%m-%d %H:%M:%S")
        ))

        # Çözülmüş veya kapatılmış taleplere çözüm notu
        if status in ("Resolved", "Closed") and resolved_at:
            resolution_messages = [
                "Gerekli teknik müdahale tamamlandı. Sorun giderildi.",
                "Yapılan kontroller sonucunda sorun çözüldü.",
                "İlgili ayarlar güncellendi ve erişim doğrulandı.",
                "Teknik işlem tamamlandı. Kullanıcı bilgilendirildi."
            ]

            resolution_time = datetime.strptime(
                resolved_at, "%Y-%m-%d %H:%M:%S"
            )

            rows.append((
                ticket_id,
                it_employee,
                random.choice(resolution_messages),
                "Resolution",
                resolution_time.strftime("%Y-%m-%d %H:%M:%S")
            ))

    cursor.executemany("""
        INSERT INTO ticket_comments (
            ticket_id,
            author_employee_id,
            comment_text,
            comment_type,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, rows)

    conn.commit()

    print(f"Eklenen yorum sayısı: {len(rows)}")

    print("\nYorum türü dağılımı:")
    for row in cursor.execute("""
        SELECT comment_type, COUNT(*)
        FROM ticket_comments
        GROUP BY comment_type
    """):
        print(row)

    print("\nYorum eklenen destek talebi:")
    print(cursor.execute("""
        SELECT COUNT(DISTINCT ticket_id)
        FROM ticket_comments
    """).fetchone()[0])

    print("\nTicket yorumları başarıyla eklendi.")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
