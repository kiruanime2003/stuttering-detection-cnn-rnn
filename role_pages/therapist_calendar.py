import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime
from sqlalchemy import create_engine, text
import os, urllib.parse
from dotenv import load_dotenv

# Load DB credentials and create engine globally
load_dotenv()
db_user = os.getenv("DB_USER")
db_pass = urllib.parse.quote(os.getenv("DB_PASS"))
db_name = os.getenv("DB_NAME")
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}")


# Dialog for creating session
@st.dialog("Create New Session")
def create_session_dialog():
    st.markdown("### Enter session details")

    title = st.text_input("Event Name")
    child_id = st.text_input("Child ID")
    session_date = st.date_input("Session Date", value=datetime.now().date())

    # Initialize session state for time inputs
    if "from_time" not in st.session_state:
        st.session_state["from_time"] = datetime.now().time()
    if "to_time" not in st.session_state:
        st.session_state["to_time"] = (datetime.now().replace(hour=datetime.now().hour + 1)).time()

    # Time inputs with persistent state
    from_time_col, to_time_col = st.columns(2)
    with from_time_col:
        st.session_state["from_time"] = st.time_input("From Time", value=st.session_state["from_time"])
    with to_time_col:
        st.session_state["to_time"] = st.time_input("To Time", value=st.session_state["to_time"])


    if st.button("✅ Confirm"):
        if not title.strip() or not child_id.strip():
            st.error("❌ All fields are required.")
        else:
            with engine.connect() as conn:
                # Validate child ID
                child_check = conn.execute(text("SELECT 1 FROM child_list WHERE child_id = :cid"), {"cid": child_id}).fetchone()
                if not child_check:
                    st.error("❌ Child ID does not exist.")
                    return

                # Get user_id from email
                user_email = st.session_state.get("email")
                user_result = conn.execute(text("SELECT user_id FROM user_list WHERE email = :email"), {"email": user_email}).fetchone()

                if not user_result:
                    st.error("❌ Logged-in user not found.")
                    return

                user_id = user_result[0]
                from_time = st.session_state["from_time"]
                to_time = st.session_state["to_time"]


                # Insert into event_list
                conn.execute(text("""
                    INSERT INTO event_list (event_name, event_date, event_from_time, event_to_time, user_id, child_id)
                    VALUES (:name, :date, :from_time, :to_time, :user_id, :child_id)
                """), {
                    "name": title,
                    "date": session_date,
                    "from_time": from_time.strftime("%H:%M:%S"),
                    "to_time": to_time.strftime("%H:%M:%S"),
                    "user_id": user_id,
                    "child_id": child_id
                })

            # Add to calendar view
            start_dt = datetime.combine(session_date, from_time)
            end_dt = datetime.combine(session_date, to_time)

            st.session_state.calendar_events.append({
                "title": f"{title} (Child ID: {child_id})",
                "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S")
            })

            st.success("✅ Session created and stored successfully!")
            st.rerun()


# Main render
def render():
    st.header("Calendar")

    # ✅ Safe session state initialization
    if "calendar_events" not in st.session_state:
        st.session_state["calendar_events"] = []

    if st.button("➕ Create Session"):
        create_session_dialog()

    calendar_options = {
        "initialView": "dayGridMonth",
        "editable": True,
        "selectable": True
    }

    calendar(events=st.session_state.calendar_events, options=calendar_options)

