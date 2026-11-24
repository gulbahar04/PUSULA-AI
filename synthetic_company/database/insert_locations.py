
import sqlite3

db_path = "synthetic_company/database/company.db"

conn = sqlite3.connect(db_path)

locations = [
    ("IST", "Istanbul Headquarters", "Istanbul", 700, 1),
    ("ANK", "Ankara Branch", "Ankara", 200, 0),
    ("IZM", "Izmir Branch", "Izmir", 150, 0)
]

conn.executemany("""
    INSERT INTO locations
    (site_id, name, city, employee_count, is_headquarters)
    VALUES (?, ?, ?, ?, ?)
""", locations)

conn.commit()

print("Lokasyon kayıtları:")
for row in conn.execute("SELECT * FROM locations"):
    print(row)

conn.close()
