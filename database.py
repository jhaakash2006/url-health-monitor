import sqlite3
from pathlib import Path


DATABASE = Path(__file__).resolve().parent / "monitor.db"


def get_connection():
    connection = sqlite3.connect(str(DATABASE))
    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            name TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            interval INTEGER NOT NULL DEFAULT 60
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            http_status INTEGER,
            response_time REAL,
            error TEXT,
            FOREIGN KEY (url_id) REFERENCES urls (id)
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_health_checks_url_id
        ON health_checks(url_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_health_checks_timestamp
        ON health_checks(timestamp)
        """
    )

    connection.commit()

    return connection


def init_database():
    connection = get_connection()

    tables = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()

    indexes = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()

    table_names = [row["name"] for row in tables]
    index_names = [row["name"] for row in indexes]

    print("Database:", DATABASE)
    print("Tables:", table_names)
    print("Indexes:", index_names)

    connection.close()


if __name__ == "__main__":
    init_database()