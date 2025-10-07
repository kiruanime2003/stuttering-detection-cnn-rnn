import streamlit as st
from sqlalchemy import create_engine
import os, urllib.parse
from dotenv import load_dotenv
import pandas as pd

def render():
    load_dotenv()
    db_user = os.getenv("DB_USER")
    db_pass = urllib.parse.quote(os.getenv("DB_PASS"))
    db_name = os.getenv("DB_NAME")
    engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}")

    def fetch_user_list():
        try:
            query = "SELECT * FROM user_list"
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            st.error(f"Error fetching user_list: {e}")
            return pd.DataFrame()
        
    def fetch_child_list():
        try:
            query = "SELECT * FROM child_list"
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            st.error(f"Error fetching child_list: {e}")
            return pd.DataFrame()

    def fetch_event_list():
        try:
            query = "SELECT * FROM event_list"
            df = pd.read_sql(query, engine)
            return df
        except Exception as e:
            st.error(f"Error fetching event_list: {e}")
            return pd.DataFrame()

    st.set_page_config(page_title="Data Viewer", layout="wide")

    st.title("User List")
    user_df = fetch_user_list()
    if not user_df.empty:
        st.dataframe(user_df, use_container_width=True)
    else:
        st.warning("No data found in the user_list table.")

    st.title("Child List")
    child_df = fetch_child_list()
    if not child_df.empty:
        st.dataframe(child_df, use_container_width=True)
    else:
        st.warning("No data found in the child_list table.")

    st.title("Event List")
    event_df = fetch_event_list()
    if not event_df.empty:
        st.dataframe(event_df, use_container_width=True)
    else:
        st.warning("No data found in the event_list table.")
