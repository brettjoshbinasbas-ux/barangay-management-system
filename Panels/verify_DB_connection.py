from Panels.db import get_connection

try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT NOW() 'current_time';")  # ✅ works for MariaDB
    result = cursor.fetchone()
    print("✅ Database connected successfully.")
    print("Current DB Time:", result["current_time"])
    cursor.close()
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e)
