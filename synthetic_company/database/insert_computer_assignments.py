
import sqlite3

DB_PATH = "synthetic_company/database/company.db"

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cursor = conn.cursor()

# Yanlışlıkla ikinci kez çalıştırılmasını önle
existing = cursor.execute(
    "SELECT COUNT(*) FROM computer_assignments"
).fetchone()[0]

if existing > 0:
    raise ValueError(
        f"Tabloda zaten {existing} atama var. "
        "Tekrar çalıştırılmadı."
    )

employees = cursor.execute("""
    SELECT employee_id, hire_date
    FROM employees
    ORDER BY employee_id
""").fetchall()

computers = cursor.execute("""
    SELECT computer_id, purchase_date
    FROM computers
    WHERE device_type IN ('Laptop', 'Desktop')
    ORDER BY computer_id
""").fetchall()

if len(employees) != 1050 or len(computers) != 1050:
    raise ValueError(
        f"Çalışan: {len(employees)}, "
        f"Bilgisayar: {len(computers)}"
    )

for employee, computer in zip(employees, computers):
    employee_id, hire_date = employee
    computer_id, purchase_date = computer

    # Atama tarihi, cihazın satın alma tarihinden önce olamaz.
    assigned_date = max(
        hire_date or purchase_date,
        purchase_date
    )

    cursor.execute("""
        INSERT INTO computer_assignments (
            computer_id,
            employee_id,
            assigned_date,
            returned_date,
            assignment_status
        )
        VALUES (?, ?, ?, NULL, 'Active')
    """, (
        computer_id,
        employee_id,
        assigned_date
    ))

conn.commit()

print("Toplam aktif bilgisayar ataması:", len(employees))

print("\nAtama kontrolü:")
for row in cursor.execute("""
    SELECT assignment_status, COUNT(*)
    FROM computer_assignments
    GROUP BY assignment_status
"""):
    print(row)

print("\nAtanmamış bilgisayar sayısı:")

unassigned = cursor.execute("""
    SELECT COUNT(*)
    FROM computers c
    LEFT JOIN computer_assignments a
        ON c.computer_id = a.computer_id
    WHERE a.assignment_id IS NULL
""").fetchone()[0]

print(unassigned)

conn.close()
