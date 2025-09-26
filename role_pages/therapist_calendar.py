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

# Load events for the logged-in user
def load_user_events():
    user_email = st.session_state.get("user_email")
    if not user_email:
        return []

    with engine.connect() as conn:
        user_row = conn.execute(
            text("SELECT user_id FROM user_list WHERE email = :email"),
            {"email": user_email}
        ).fetchone()
        if not user_row:
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

# Create new session dialog
@st.dialog("Create New Session")
def create_session_dialog():
    st.markdown("### Enter session details")

    title = st.text_input("Event Name")
    child_id = st.text_input("Child ID")
    session_date = st.date_input("Session Date", value=datetime.now().date())

    now = datetime.now()
    if "from_time" not in st.session_state:
        st.session_state["from_time"] = now.time()
    if "to_time" not in st.session_state:
        st.session_state["to_time"] = (now + timedelta(hours=1)).time()

    from_col, to_col = st.columns(2)
    with from_col:
        st.session_state["from_time"] = st.time_input("From Time", value=st.session_state["from_time"], key="from_time_input")
    with to_col:
        st.session_state["to_time"] = st.time_input("To Time", value=st.session_state["to_time"], key="to_time_input")

    if st.button("✅ Confirm"):
        if not title.strip() or not child_id.strip():
            st.error("❌ All fields are required.")
            return

        start_dt = datetime.combine(session_date, st.session_state["from_time"])
        end_dt = datetime.combine(session_date, st.session_state["to_time"])
        now = datetime.now()

        if session_date < now.date():
            st.error("❌ Cannot create events in the past.")
            return
        if session_date == now.date() and start_dt < now:
            st.error("❌ Start time must be in the future.")
            return
        if end_dt <= start_dt:
            st.error("❌ End time must be after start time.")
            return

        user_email = st.session_state.get("user_email")
        if not user_email:
            st.error("❌ No user email found in session.")
            return

        try:
            with engine.begin() as conn:
                child_check = conn.execute(
                    text("SELECT 1 FROM child_list WHERE child_id = :cid"),
                    {"cid": child_id}
                ).fetchone()
                if not child_check:
                    st.error("❌ Child ID does not exist.")
                    return

                user_row = conn.execute(
                    text("SELECT user_id FROM user_list WHERE email = :email"),
                    {"email": user_email}
                ).fetchone()
                if not user_row:
                    st.error("❌ User not found.")
                    return

                user_id = user_row[0]

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

        st.success("✅ Session created successfully!")
        st.rerun()

# Edit session dialog
@st.dialog("Edit Session")
def edit_session_dialog():
    event = st.session_state.get("selected_event")
    if not event:
        st.warning("⚠️ No event selected.")
        return

    title = event["title"].split(" (Child ID")[0]
    child_id = event["title"].split("Child ID: ")[-1].rstrip(")")
    start_dt = datetime.fromisoformat(event["start"])
    end_dt = datetime.fromisoformat(event["end"])

    new_title = st.text_input("Event Name", value=title)
    new_child_id = st.text_input("Child ID", value=child_id)
    new_date = st.date_input("Session Date", value=start_dt.date())

    from_col, to_col = st.columns(2)
    with from_col:
        new_from_time = st.time_input("From Time", value=start_dt.time(), key="edit_from_time")
    with to_col:
        new_to_time = st.time_input("To Time", value=end_dt.time(), key="edit_to_time")

    if st.button("💾 Save Changes"):
        now = datetime.now()
        new_start = datetime.combine(new_date, new_from_time)
        new_end = datetime.combine(new_date, new_to_time)

        if new_date < now.date():
            st.error("❌ Cannot set past dates.")
            return
        if new_date == now.date() and new_start < now:
            st.error("❌ Start time must be in the future.")
            return
        if new_end <= new_start:
            st.error("❌ End time must be after start time.")
            return

        user_email = st.session_state.get("user_email")
        with engine.begin() as conn:
            user_row = conn.execute(
                text("SELECT user_id FROM user_list WHERE email = :email"),
                {"email": user_email}
            ).fetchone()
            user_id = user_row[0] if user_row else None

            conn.execute(text("""
                UPDATE event_list
                SET event_name = :name,
                    event_date = :date,
                    event_from_time = :from_time,
                    event_to_time = :to_time,
                    child_id = :child_id
                WHERE user_id = :user_id
                  AND event_name = :old_name
                  AND event_date = :old_date
                  AND event_from_time = :old_from
            """), {
                "name": new_title,
                "date": new_date,
                "from_time": new_from_time.strftime("%H:%M:%S"),
                "to_time": new_to_time.strftime("%H:%M:%S"),
                "child_id": new_child_id,
                "user_id": user_id,
                "old_name": title,
                "old_date": start_dt.date(),
                "old_from": start_dt.time().strftime("%H:%M:%S")
            })

        st.success("✅ Event updated!")
        st.session_state["edit_mode"] = False
        st.rerun()

# Main render
def render():
    st.header("Calendar")

    if "calendar_events" not in st.session_state:
        st.session_state["calendar_events"] = []

    st.session_state["calendar_events"] = load_user_events()

    calendar_response = calendar(
        events=st.session_state["calendar_events"],
        options={
            "initialView": "dayGridMonth",
            "editable": True,
            "selectable": True
        }
    )

    if calendar_response and "eventClick" in calendar_response:
        clicked_event = calendar_response["eventClick"].get("event")
        if clicked_event and "title" in clicked_event and "start" in clicked_event and "end" in clicked_event:
            st.session_state["selected_event"] = clicked_event
            st.session_state["edit_mode"] = True


    if st.button("➕ Create Session"):
        create_session_dialog()

    if st.session_state.get("edit_mode", False):
        edit_session_dialog()


render()
