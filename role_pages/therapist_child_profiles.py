import streamlit as st
from sqlalchemy import create_engine, text
import os, urllib.parse
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
db_user = os.getenv("DB_USER")
db_pass = urllib.parse.quote(os.getenv("DB_PASS"))
db_name = os.getenv("DB_NAME")
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}")

def render():
    st.header("Child Profiles")

    st.write("Logged in as:", st.session_state.get("user_email", "Not logged in"))

    if "show_form" not in st.session_state:
        st.session_state.show_form = False

    if st.button("➕ New"):
        st.session_state.show_form = True

    if st.session_state.show_form:
        if st.button("❌ Close"):
            st.session_state.show_form = False

    if st.session_state.show_form:
        # Resolve therapist_id
        therapist_id = None
        current_email = st.session_state.get("user_email")
        if current_email:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT user_id FROM user_list WHERE email = :email"),
                    {"email": current_email}
                )
                therapist_row = result.fetchone()
                therapist_id = therapist_row[0] if therapist_row else None
        else:
            st.warning("No user email found in session. Please log in.")

        st.markdown("### Add New Child Profile")

        with st.form("new_child_form"):
            st.text_input("Therapist ID", value=str(therapist_id), disabled=True)
            full_name = st.text_input("Full Name")
            parent_email = st.text_input("Parent Email")
            age = st.number_input("Age", min_value=1, max_value=18, step=1)
            place = st.text_input("Place")

            submitted = st.form_submit_button("Submit")
            if submitted:
                recent_visit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    with engine.begin() as conn:
                        result = conn.execute(text("""
                            INSERT INTO child_list (
                                therapist_id, recent_visit_date, full_name,
                                parent_email, age, place
                            ) VALUES (
                                :therapist_id, :recent_visit_date, :full_name,
                                :parent_email, :age, :place
                            )
                        """), {
                            "therapist_id": therapist_id,
                            "recent_visit_date": recent_visit_date,
                            "full_name": full_name,
                            "parent_email": parent_email,
                            "age": age,
                            "place": place
                        })

                        # Get the newly generated child_id
                        new_child_id = result.lastrowid  

                    st.success(f"✅ Child profile added successfully! (Child ID: {new_child_id})")
                    st.session_state.show_form = False

                except Exception as e:
                    st.error(f"❌ Insert failed: {e}")
