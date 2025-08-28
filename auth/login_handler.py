# auth_manage.py
from sqlalchemy import text

def get_user_role(conn, email):
    result = conn.execute(
        text("SELECT role FROM user_list WHERE email = :e"),
        {"e": email}
    ).fetchone()
    return result[0] if result else None

def validate_login(conn, email, password):
    result = conn.execute(
        text("SELECT password FROM user_list WHERE email = :e"),
        {"e": email}
    ).fetchone()
    return result and result[0] == password

def register_user(conn, email, password, role):
    conn.execute(
        text("INSERT INTO user_list (email, password, role) VALUES (:e, :p, :r)"),
        {"e": email, "p": password, "r": role}
    )
    conn.commit()
