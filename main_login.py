from auth.login_handler import get_user_role, validate_login, register_user
from auth.session_manager import login_user, logout_user

import streamlit as st
from sqlalchemy import create_engine
import os, urllib.parse
from dotenv import load_dotenv

# DB setup
load_dotenv()
db_user = os.getenv("DB_USER")
db_pass = urllib.parse.quote(os.getenv("DB_PASS"))
db_name = os.getenv("DB_NAME")
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}")

# Role-based page map
role_pages = {
    "Admin": {
        "Accounts": "admin_accounts",
        "Models": "admin_models"
    },
    "Therapist": {
        "Home": "therapist_home",
        "Calendar": "therapist_calendar",
        "Child profiles": "therapist_child_profiles"
    },
    "Parent": {
        "Dashboard": "parent"
    }
}

# UI
st.set_page_config(page_title="Stuttering Detection App", layout="centered")

if not st.session_state.get("logged_in"):
    st.title("Stuttering Detection App")

    email = st.text_input("Email")

    if email:
        with engine.begin() as conn:
            role = get_user_role(conn, email)

        if role:
            st.info(f"Account found. Role: {role}")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                with engine.begin() as conn:
                    if validate_login(conn, email, password):
                        login_user(email, role)
                        st.session_state.logged_in = True
                        st.session_state.role = role
                        st.success("Logged in!")
                        st.rerun()  # ← rerun to hide login form
                    else:
                        st.error("Incorrect password.")
        else:
            st.warning("New account will be created.")
            role = st.selectbox("Select role", ("Admin", "Therapist", "Parent"))
            password = st.text_input("Create Password", type="password")
            if st.button("Register"):
                with engine.begin() as conn:
                    register_user(conn, email, password, role)
                    login_user(email, role)
                    st.session_state.logged_in = True
                    st.session_state.role = role
                    st.success("Account created!")
                    st.rerun()  # ← rerun to hide registration form


# Role-based navigation
if st.session_state.get("logged_in"):
    role = st.session_state["role"]
    page_options = list(role_pages[role].keys())
    selected_page = st.sidebar.radio("Navigation", page_options)

    if st.sidebar.button("Logout"):
        logout_user()
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    module_name = role_pages[role][selected_page]
    module = __import__(f"role_pages.{module_name}", fromlist=["render"])
    module.render()