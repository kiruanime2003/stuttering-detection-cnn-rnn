import streamlit as st

def render():
    st.header("Homepage")
    # Upload and record section
    upload, record = st.columns(2, vertical_alignment="top")
    with upload:
        uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3"])

    with record:
        audio_file = st.audio_input("Record your voice")

    st.write(" ")
    st.write(" ")

    # Predict button
    st.button("Predict", type="primary", key="predict")