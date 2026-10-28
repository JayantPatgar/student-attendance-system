"""Create required tables and an initial admin account.

Set ADMIN_USERNAME and ADMIN_PASSWORD before running this script.
"""
import os
from pathlib import Path
from werkzeug.security import generate_password_hash
from database import get_db_connection


def main():
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        raise SystemExit(
            "Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables before running init_db.py."
        )
    if len(password) < 8:
        raise SystemExit("ADMIN_PASSWORD must contain at least 8 characters.")

    sql = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        cursor.execute("SELECT id FROM admin WHERE username = %s", (username,))
        existing = cursor.fetchone()
        if existing:
            print(f"Admin account '{username}' already exists; password was not changed.")
        else:
            cursor.execute(
                "INSERT INTO admin (username, password) VALUES (%s, %s)",
                (username, generate_password_hash(password)),
            )
            print(f"Created admin account '{username}'.")
        connection.commit()
        print("Database tables are ready.")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
