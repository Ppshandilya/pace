# database.py
import MySQLdb
from contextlib import contextmanager

@contextmanager
def get_cursor():
    conn = MySQLdb.connect(host="localhost", user="root", passwd="Mrinal", db="mysql")
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        cursor.close()
        conn.close()
