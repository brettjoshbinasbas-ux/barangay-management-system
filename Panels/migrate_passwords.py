import bcrypt
from Panels.db import get_connection

def hash_password_if_needed(password: str) -> str:
    """
    Check if password is already bcrypt hashed.
    If not, hash and return.
    """
    # bcrypt hashes usually start with $2b$ or $2a$
    if password.startswith("$2"):
        return password  # already hashed
    # otherwise, hash it
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def migrate_table(table_name: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, username, password FROM {table_name}")
    users = cursor.fetchall()

    updated = 0
    for user in users:
        user_id = user["id"]
        username = user["username"]
        current_pw = user["password"]

        new_pw = hash_password_if_needed(current_pw)

        if new_pw != current_pw:  # only update if changed
            cursor.execute(f"UPDATE {table_name} SET password=%s WHERE id=%s", (new_pw, user_id))
            updated += 1
            print(f"[{table_name}] Updated {username}'s password → bcrypt hash")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"✅ Migration done for {table_name}: {updated} password(s) updated.")


if __name__ == "__main__":
    migrate_table("staff")
    migrate_table("admins")
    print("🎉 All passwords are now bcrypt hashed.")
