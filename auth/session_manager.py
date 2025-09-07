import streamlit as st

def login_user(email, role):
    st.session_state["user_email"] = email
    st.session_state["role"] = role
    st.session_state["logged_in"] = True

def logout_user():
    for key in ["email", "role", "logged_in"]:
        st.session_state.pop(key, None)

def logout_user():
    # Optional: Add logging or cleanup logic here
    pass  # You can expand this later if needed

