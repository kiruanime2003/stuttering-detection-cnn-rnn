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

# Dialog for adding a new child
@st.dialog("Add New Child Profile")
def show_child_form(therapist_id):
    with st.form("new_child_form"):
        st.text_input("Therapist ID", value=str(therapist_id), disabled=True)
        full_name = st.text_input("Full Name")
        parent_email = st.text_input("Parent Email")
        age = st.number_input("Age", min_value=1, max_value=18, step=1)
        place = st.text_input("Place")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if not full_name.strip() or not parent_email.strip() or not place.strip():
                st.error("❌ All fields are required.")
            else:
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

                        new_child_id = result.lastrowid

                    st.success(f"✅ Child profile added successfully! (Child ID: {new_child_id})")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Insert failed: {e}")

# Dialog for editing an existing child
@st.dialog("Edit Child Profile")
def edit_child_form(child):
    with st.form(f"edit_child_form_{child.child_id}"):
        st.text_input("Child ID", value=str(child.child_id), disabled=True)
        full_name = st.text_input("Full Name", value=child.full_name)
        parent_email = st.text_input("Parent Email", value=child.parent_email)
        age = st.number_input("Age", min_value=1, max_value=18, step=1, value=child.age)
        place = st.text_input("Place", value=child.place)
        submitted = st.form_submit_button("Update")

        if submitted:
            if not full_name.strip() or not parent_email.strip() or not place.strip():
                st.error("❌ All fields are required.")
            else:
                try:
                    with engine.begin() as conn:
                        conn.execute(text("""
                            UPDATE child_list
                            SET full_name = :full_name,
                                parent_email = :parent_email,
                                age = :age,
                                place = :place
                            WHERE child_id = :child_id
                        """), {
                            "full_name": full_name,
                            "parent_email": parent_email,
                            "age": age,
                            "place": place,
                            "child_id": child.child_id
                        })

                    st.success("✅ Child profile updated successfully!")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Update failed: {e}")

def render():
    st.header("Child Profiles")

    st.write("Logged in as:", st.session_state.get("user_email", "Not logged in"))

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

    # Show dialog when button is clicked
    if st.button("➕ New") and therapist_id:
        show_child_form(therapist_id)

    # Inject CSS for hover-based edit icon
    st.markdown("""
        <style>
        .card-container {
            position: relative;
            border: 1px solid #ccc;
            border-radius: 10px;
            padding: 20px;
            margin: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            transition: box-shadow 0.3s ease;
        }
        .card-container:hover {
            box-shadow: 4px 4px 10px rgba(0,0,0,0.2);
        }
        .edit-button {
            position: absolute;
            top: 10px;
            right: 10px;
            display: none;
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
        }
        .card-container:hover .edit-button {
            display: block;
        }
        </style>
    """, unsafe_allow_html=True)

    # Show child cards
    if therapist_id:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT child_id, full_name, age, recent_visit_date, parent_email, place
                FROM child_list
                WHERE therapist_id = :therapist_id
                ORDER BY recent_visit_date DESC
            """), {"therapist_id": therapist_id})

            children = result.fetchall()

        if children:
            cols = st.columns(3)
            for idx, child in enumerate(children):
                if idx % 3 == 0:
                    cols = st.columns(3)
                with cols[idx % 3]:
                    st.markdown(
                        f"""
                        <div class="card-container">
                            <h4 style="margin: 0;">{child.full_name}</h4>
                            <p><b>Child ID:</b> {child.child_id}</p>
                            <p><b>Age:</b> {child.age}</p>
                            <p><b>Last Visit:</b> {child.recent_visit_date}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button("✏️ Edit", key=f"edit_{child.child_id}"):
                        edit_child_form(child)

                    else:
                        st.info("No children added yet.")
