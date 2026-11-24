
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
conn.execute("PRAGMA foreign_keys = ON")

nesting = [
    # Global Group -> Domain Local Group
    ("G014", "G001"),  # Finance -> Finance File RW
    ("G015", "G002"),  # HR -> HR File RW
    ("G016", "G003"),  # Sales -> Sales File RO
    ("G017", "G010"),  # IT Support -> Server Management
    ("G017", "G011"),  # System Admins -> Server Management
    ("G017", "G012"),  # Network Admins -> Server Management
    ("G017", "G013")   # Security Admins -> Server Management
]

conn.executemany("""
    INSERT INTO group_nesting (parent_group_id, child_group_id)
    VALUES (?, ?)
""", nesting)

conn.commit()

print("Toplam grup ilişkisi:", conn.execute(
    "SELECT COUNT(*) FROM group_nesting"
).fetchone()[0])

print("\nGrup ilişkileri:")
for row in conn.execute("""
    SELECT parent.group_name, child.group_name
    FROM group_nesting gn
    JOIN ad_groups parent ON gn.parent_group_id = parent.group_id
    JOIN ad_groups child ON gn.child_group_id = child.group_id
"""):
    print(f"{row[1]} -> {row[0]}")

conn.close()
