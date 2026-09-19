import sqlite3

from app.config import DATA_DIR, DB_FILENAME

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / DB_FILENAME


def connect() -> sqlite3.Connection:
    # autocommit：写操作各自显式 commit；需要原子性的流程显式 BEGIN/COMMIT
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn
