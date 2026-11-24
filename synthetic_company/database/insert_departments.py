
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")

departments = [
    ("IT", "Information Technology", 10),
    ("FIN", "Finance", 140),
    ("HR", "Human Resources", 60),
    ("SALES", "Sales", 290),
    ("OPS", "Operations", 435),
    ("MGMT", "Management & Corporate", 115)
]

conn.executemany("""
    INSERT INTO departments (dept_id, name, employee_count)
    VALUES (?, ?, ?)
""", departments)

conn.commit()

print("Departman kayıtları:")
for row in conn.execute("SELECT * FROM departments"):
    print(row)

conn.close()
