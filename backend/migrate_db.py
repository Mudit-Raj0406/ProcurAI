import sqlite3
import os

db_path = 'procurai_v2.db'

def migrate():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check bids table columns
    cursor.execute("PRAGMA table_info(bids)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns in bids: {columns}")

    needed_columns = [
        ('project_id', 'INTEGER'),
        ('incoterms', 'TEXT'),
        ('warranty_terms', 'TEXT'),
        ('is_iatf_certified', 'BOOLEAN DEFAULT 0'),
        ('risk_flags', 'TEXT'),
        ('score', 'FLOAT DEFAULT 0.0'),
        ('reviewer_comments', 'TEXT'),
        ('status', 'TEXT')
    ]

    for col_name, col_type in needed_columns:
        if col_name not in columns:
            print(f"Adding column {col_name} to bids...")
            try:
                cursor.execute(f"ALTER TABLE bids ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")

    # Ensure projects table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    if not cursor.fetchone():
        print("Creating projects table...")
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rfq_id TEXT UNIQUE,
                title TEXT,
                category TEXT,
                description TEXT,
                status TEXT DEFAULT 'Open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Check extracted_items table columns
    cursor.execute("PRAGMA table_info(extracted_items)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Current columns in extracted_items: {columns}")

    needed_item_columns = [
        ('material_spec', 'TEXT'),
        ('part_number', 'TEXT')
    ]

    for col_name, col_type in needed_item_columns:
        if col_name not in columns:
            print(f"Adding column {col_name} to extracted_items...")
            try:
                cursor.execute(f"ALTER TABLE extracted_items ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name} to extracted_items: {e}")

    # Check projects table columns
    cursor.execute("PRAGMA table_info(projects)")
    columns = [row[1] for row in cursor.fetchall()]
    
    needed_project_columns = [
        ('rfq_raw_text', 'TEXT'),
        ('rfq_requirements', 'TEXT')
    ]

    for col_name, col_type in needed_project_columns:
        if col_name not in columns:
            print(f"Adding column {col_name} to projects...")
            try:
                cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}")
            except Exception as e:
                print(f"Error adding {col_name} to projects: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
