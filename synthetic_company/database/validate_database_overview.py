
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

tables = cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name
""").fetchall()

print("VERİTABANI TABLO ENVANTERİ")
print("-" * 45)

total_records = 0

for (table,) in tables:
    count = cursor.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    ).fetchone()[0]

    total_records += count
    print(f"{table}: {count}")

integrity = cursor.execute(
    "PRAGMA integrity_check"
).fetchone()[0]

foreign_key_errors = cursor.execute(
    "PRAGMA foreign_key_check"
).fetchall()

print("\nGENEL KONTROLLER")
print("-" * 45)
print(f"Toplam tablo: {len(tables)}")
print(f"Toplam kayıt: {total_records}")
print(f"SQLite integrity_check: {integrity}")
print(f"Foreign key hatası: {len(foreign_key_errors)}")

print("\nSONUÇ:")
if integrity == "ok" and len(foreign_key_errors) == 0:
    print("GENEL VERİTABANI KONTROLLERİ BAŞARILI.")
else:
    print("VERİTABANINDA HATA BULUNDU.")

if foreign_key_errors:
    print("\nForeign key hataları:")
    for error in foreign_key_errors:
        print(error)

conn.close()