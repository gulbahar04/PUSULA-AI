
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
conn.execute("PRAGMA foreign_keys = ON")

# Ankara ve İzmir'deki mevcut çalışanlardan irtibat kişileri seç
contacts = [
    ("SC001", "EMP0151", "ANK", "Branch IT Coordination", 0),
    ("SC002", "EMP0351", "IZM", "Branch IT Coordination", 0)
]

conn.executemany("""
    INSERT INTO site_contacts (
        contact_id, employee_id, site_id,
        responsibility, is_it_employee
    )
    VALUES (?, ?, ?, ?, ?)
""", contacts)

conn.commit()

print("Şube irtibat kişileri:")
for row in conn.execute("""
    SELECT sc.contact_id, e.first_name, e.last_name,
           d.name, l.city, sc.is_it_employee
    FROM site_contacts sc
    JOIN employees e ON sc.employee_id = e.employee_id
    JOIN departments d ON e.dept_id = d.dept_id
    JOIN locations l ON sc.site_id = l.site_id
"""):
    print(row)

conn.close()
