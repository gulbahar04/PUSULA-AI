
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

total = cursor.execute(
    "SELECT COUNT(*) FROM ticket_comments"
).fetchone()[0]

invalid_ticket = cursor.execute("""
    SELECT COUNT(*)
    FROM ticket_comments c
    LEFT JOIN tickets t ON c.ticket_id = t.ticket_id
    WHERE t.ticket_id IS NULL
""").fetchone()[0]

invalid_author = cursor.execute("""
    SELECT COUNT(*)
    FROM ticket_comments c
    LEFT JOIN employees e
      ON c.author_employee_id = e.employee_id
    WHERE e.employee_id IS NULL
""").fetchone()[0]

invalid_user_message = cursor.execute("""
    SELECT COUNT(*)
    FROM ticket_comments c
    JOIN tickets t ON c.ticket_id = t.ticket_id
    WHERE c.comment_type = 'UserMessage'
      AND c.author_employee_id != t.employee_id
""").fetchone()[0]

invalid_it_response = cursor.execute("""
    SELECT COUNT(*)
    FROM ticket_comments c
    JOIN tickets t ON c.ticket_id = t.ticket_id
    JOIN ad_users a ON t.assigned_ad_user_id = a.ad_user_id
    WHERE c.comment_type IN ('ITResponse', 'Resolution')
      AND c.author_employee_id != a.employee_id
""").fetchone()[0]

invalid_dates = cursor.execute("""
    SELECT COUNT(*)
    FROM ticket_comments c
    JOIN tickets t ON c.ticket_id = t.ticket_id
    WHERE c.created_at < t.created_at
       OR c.created_at > t.updated_at
""").fetchone()[0]

missing_user_messages = cursor.execute("""
    SELECT COUNT(*)
    FROM tickets t
    WHERE NOT EXISTS (
        SELECT 1 FROM ticket_comments c
        WHERE c.ticket_id = t.ticket_id
          AND c.comment_type = 'UserMessage'
    )
""").fetchone()[0]

checks = {
    "Toplam yorum": total == 2601,
    "Geçersiz destek talebi": invalid_ticket == 0,
    "Geçersiz yorum yazarı": invalid_author == 0,
    "Kullanıcı mesajı eşleşmesi": invalid_user_message == 0,
    "IT personeli eşleşmesi": invalid_it_response == 0,
    "Geçersiz yorum tarihi": invalid_dates == 0,
    "Eksik kullanıcı mesajı": missing_user_messages == 0
}

print(f"Toplam yorum: {total}")
print(f"Geçersiz destek talebi: {invalid_ticket}")
print(f"Geçersiz yorum yazarı: {invalid_author}")
print(f"Kullanıcı mesajı eşleşme hatası: {invalid_user_message}")
print(f"IT personeli eşleşme hatası: {invalid_it_response}")
print(f"Geçersiz yorum tarihi: {invalid_dates}")
print(f"Kullanıcı mesajı eksik talep: {missing_user_messages}")

print("\nSONUÇ:")
if all(checks.values()):
    print("TÜM TICKET COMMENT KONTROLLERİ BAŞARILI.")
else:
    print("BAZI KONTROLLER BAŞARISIZ.")

conn.close()
