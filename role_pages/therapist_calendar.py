import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import os, urllib.parse
from dotenv import load_dotenv

# Load DB credentials and create engine globally
load_dotenv()
db_user = os.getenv("DB_USER")
db_pass = urllib.parse.quote(os.getenv("DB_PASS"))
db_name = os.getenv("DB_NAME")
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}")

# Function to load events for the logged-in user
def load_user_events():
    user_email = st.session_state.get("user_email")
    if not user_email:
        st.warning("⚠️ Please log in to view your calendar.")
        return []

    with engine.connect() as conn:
        user_row = conn.execute(
            text("SELECT user_id FROM user_list WHERE email = :email"),
            {"email": user_email}
        ).fetchone()
        if not user_row:
            st.warning("⚠️ User not found.")
            return []

        user_id = user_row[0]
        rows = conn.execute(
            text("""
                SELECT event_name, event_date, event_from_time, event_to_time, child_id
                FROM event_list
                WHERE user_id = :uid
            """),
            {"uid": user_id}
        ).fetchall()

    events = []
    for row in rows:
    # Convert timedelta → time
        from_time = (datetime.min + row.event_from_time).time() if isinstance(row.event_from_time, timedelta) else row.event_from_time
        to_time = (datetime.min + row.event_to_time).time() if isinstance(row.event_to_time, timedelta) else row.event_to_time

        start_dt = datetime.combine(row.event_date, from_time)
        end_dt = datetime.combine(row.event_date, to_time)

        events.append({
            "title": f"{row.event_name} (Child ID: {row.child_id})",
            "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        })

    return events

# Dialog for creating session
@st.dialog("Create New Session")
def create_session_dialog():
    st.markdown("### Enter session details")

    title = st.text_input("Event Name")
    child_id = st.text_input("Child ID")
    session_date = st.date_input("Session Date", value=datetime.now().date())

    # Initialize session state for time inputs only once
    now = datetime.now()
    if "from_time" not in st.session_state:
        st.session_state["from_time"] = now.time()
    if "to_time" not in st.session_state:
        st.session_state["to_time"] = (now + timedelta(hours=1)).time()

    from_time_col, to_time_col = st.columns(2)
    with from_time_col:
        st.session_state["from_time"] = st.time_input("From Time", value=st.session_state["from_time"], key="from_time_input")
    with to_time_col:
        st.session_state["to_time"] = st.time_input("To Time", value=st.session_state["to_time"], key="to_time_input")

    if st.button("✅ Confirm"):
        if not title.strip() or not child_id.strip():
            st.error("❌ All fields are required.")
            return

        start_dt = datetime.combine(session_date, st.session_state["from_time"])
        end_dt = datetime.combine(session_date, st.session_state["to_time"])

        user_email = st.session_state.get("user_email")
        if not user_email:
            st.error("❌ No user email found in session. Please log in.")
            return

        try:
            with engine.begin() as conn:
                # Validate child ID
                child_check = conn.execute(
                    text("SELECT 1 FROM child_list WHERE child_id = :cid"),
                    {"cid": child_id}
                ).fetchone()
                if not child_check:
                    st.error("❌ Child ID does not exist.")
                    return

                # Get user_id from user_list
                user_row = conn.execute(
                    text("SELECT user_id FROM user_list WHERE email = :email"),
                    {"email": user_email}
                ).fetchone()
                if not user_row:
                    st.error("❌ User not found in user_list.")
                    return

                user_id = user_row[0]

                # Insert event
                conn.execute(text("""
                    INSERT INTO event_list (
                        event_name, event_date, event_from_time, event_to_time, user_id, child_id
                    ) VALUES (
                        :name, :date, :from_time, :to_time, :user_id, :child_id
                    )
                """), {
                    "name": title,
                    "date": session_date,
                    "from_time": st.session_state["from_time"].strftime("%H:%M:%S"),
                    "to_time": st.session_state["to_time"].strftime("%H:%M:%S"),
                    "user_id": user_id,
                    "child_id": child_id
                })

        except Exception as e:
            st.error(f"❌ Failed to insert event: {e}")
            return

        st.success("✅ Session created and stored successfully!")
        st.rerun()

# Main render
def render():
    st.header("Calendar")

    # ✅ Safe session state initialization
    if "calendar_events" not in st.session_state:
        st.session_state["calendar_events"] = []

    # Load events for the logged-in user
    st.session_state["calendar_events"] = load_user_events()

    if st.button("➕ Create Session"):
        create_session_dialog()

    calendar_options = {
        "initialView": "dayGridMonth",
        "editable": True,
        "selectable": True
    }

    calendar(events=st.session_state["calendar_events"], options=calendar_options)

render()
