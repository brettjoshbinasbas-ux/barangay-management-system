# Panels/db.py
import pymysql
from pymysql.cursors import DictCursor
import bcrypt   # ✅ add this

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="brms_db",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )

# ✅ Hash a plain text password
def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")

# ✅ Verify a plain text password against a hashed one
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False
