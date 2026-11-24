
import sqlite3
from datetime import date, timedelta

DB_PATH = "synthetic_company/database/company.db"

# Departman ve lokasyon dağılımı
distribution = {
    "IT": {"IST": 10},
    "FIN": {"IST": 100, "ANK": 25, "IZM": 15},
    "HR": {"IST": 45, "ANK": 10, "IZM": 5},
    "SALES": {"IST": 180, "ANK": 65, "IZM": 45},
    "OPS": {"IST": 280, "ANK": 85, "IZM": 70},
    "MGMT": {"IST": 85, "ANK": 15, "IZM": 15}
}

first_names = [
    "Ahmet", "Mehmet", "Mustafa", "Emre", "Can",
    "Burak", "Mert", "Kerem", "Ali", "Onur",
    "Ayşe", "Fatma", "Zeynep", "Elif", "Bahar",
    "Esra", "Merve", "Selin", "Ece", "Deniz"
]

last_names = [
    "Yılmaz", "Kaya", "Demir", "Şahin", "Çelik",
    "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
    "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin",
    "Kara", "Koç", "Kurt", "Polat", "Aksoy"
]

employees = []
employee_number = 1
department_managers = {}

for dept_id, sites in distribution.items():
    for site_id, count in sites.items():
        for _ in range(count):
            employee_id = f"EMP{employee_number:04d}"

            first_name = first_names[(employee_number - 1) % len(first_names)]
            last_name = last_names[
                ((employee_number - 1) // len(first_names)) % len(last_names)
            ]

            # Her departmanın ilk çalışanı departman yöneticisi
            if dept_id not in department_managers:
                department_managers[dept_id] = employee_id
                job_title = "Department Manager"
                manager_id = None
            else:
                job_title = "Employee"
                manager_id = department_managers[dept_id]

            hire_date = date(2018, 1, 1) + timedelta(days=employee_number)

            employees.append((
                employee_id,
                first_name,
                last_name,
                dept_id,
                site_id,
                job_title,
                hire_date.isoformat(),
                None,
                "Active",
                manager_id
            ))

            employee_number += 1

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

conn.executemany("""
    INSERT INTO employees (
        employee_id, first_name, last_name, dept_id,
        site_id, job_title, hire_date,
        termination_date, employment_status, manager_id
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", employees)

conn.commit()

print("Toplam çalışan:", conn.execute(
    "SELECT COUNT(*) FROM employees"
).fetchone()[0])

print("\nDepartmanlara göre çalışan sayısı:")
for row in conn.execute("""
    SELECT d.name, COUNT(e.employee_id)
    FROM employees e
    JOIN departments d ON e.dept_id = d.dept_id
    GROUP BY d.dept_id
"""):
    print(row)

print("\nLokasyonlara göre çalışan sayısı:")
for row in conn.execute("""
    SELECT l.city, COUNT(e.employee_id)
    FROM employees e
    JOIN locations l ON e.site_id = l.site_id
    GROUP BY l.site_id
"""):
    print(row)

conn.close()
