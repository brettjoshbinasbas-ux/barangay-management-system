# create_test_users.py
import bcrypt
from Panels.db import get_connection

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_test_users():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # ✅ Test Admin
        cursor.execute("INSERT INTO admins (username, password, email) VALUES (%s, %s, %s)", (
            "admin_test",
            hash_password("AdminPass123!"),
            "admin_test@example.com"
        ))

        # ✅ Test Staff
        cursor.execute("INSERT INTO staff (username, password, email, role, status) VALUES (%s, %s, %s, %s, %s)", (
            "staff_test",
            hash_password("StaffPass123!"),
            "staff_test@example.com",
            "Staff/Worker",
            "active"
        ))

        conn.commit()
        cursor.close()
        conn.close()

        print("✅ Created admin: admin_test / AdminPass123!")
        print("✅ Created staff: staff_test / StaffPass123!")

    except Exception as e:
        print(f"⚠️ Failed to create test users: {e}")

if __name__ == "__main__":
    create_test_users()
