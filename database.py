import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


def _get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _init_db():
    with _get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                lives INTEGER DEFAULT 5,
                coins INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0
            )
            """
        )


def add_user(user_id, username):
    with _get_connection() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        connection.commit()


def get_user_stats(user_id):
    with _get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT user_id, username, lives, coins, wins, losses
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


_init_db()
