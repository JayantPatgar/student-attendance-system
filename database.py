"""Database connection configuration for local development and Render."""
import os
import mysql.connector


def get_db_connection():
    """Connect using environment variables; local defaults support MySQL on Windows."""
    ssl_disabled = os.getenv("DB_SSL_DISABLED", "false").strip().lower() in {"1", "true", "yes"}
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "Attendance_db1"),
        connection_timeout=10,
        ssl_disabled=ssl_disabled,
    )
