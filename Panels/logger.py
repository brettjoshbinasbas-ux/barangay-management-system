from Panels.db import get_connection

def log_staff_activity(staff_id, action_type, description, role="Staff"):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO staff_activity (staff_id, role, action_type, description)
            VALUES (%s, %s, %s, %s)
        """, (staff_id, role, action_type, description))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log staff activity: {e}")



def log_admin_activity(admin_id, action_type, description):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO admin_activity (admin_id, action_type, description)
            VALUES (%s, %s, %s)
        """, (admin_id, action_type, description))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to log admin activity: {e}")
