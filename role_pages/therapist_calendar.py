import streamlit as st
from streamlit_calendar import calendar
def render():
    st.header("Calendar")
    calendar_options = {
        "initialView": "dayGridMonth",
        "editable": True,
        "selectable": True
    }

    calendar_events = [
        {"title": "Therapy Session", "start": "2025-08-28T10:00:00", "end": "2025-08-28T11:00:00"},
        {"title": "Parent Meeting", "start": "2025-08-29T14:00:00"}
    ]

    calendar(events=calendar_events, options=calendar_options)
