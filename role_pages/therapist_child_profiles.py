import streamlit as st

def render():
    st.header("Child profiles")
    st.button("➕ New", use_container_width=True)
    st.write("View list of clients")

    children = [
        {
            "child_id": "C001",
            "name": "Aarav Sharma",
            "age": 7,
            "last_visit": "2025-08-28"
        },
        {
            "child_id": "C002",
            "name": "Meera Iyer",
            "age": 6,
            "last_visit": "2025-09-02"
        },
        {
            "child_id": "C003",
            "name": "Aditya Singh",
            "age": 8,
            "last_visit": "2025-08-22"
        }
        # Add more children as needed
    ]

    cols_per_row = 3  # Number of cards per row
    num_children = len(children)
    num_rows = (num_children + cols_per_row - 1) // cols_per_row

    for r in range(num_rows):
        cols = st.columns(cols_per_row)
        for c in range(cols_per_row):
            idx = r * cols_per_row + c
            if idx >= num_children:
                break
            child = children[idx]
            with cols[c]:
                st.markdown(
                    f"""
                    <div style="
                        border: 2px solid #ccc;
                        border-radius: 10px;
                        padding: 15px;
                        margin: 10px 0;
                        width: 90%;
                        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                        background-color: #f9f9f9;
                    ">
                        <h4 style="margin-top:10px;">{child['name']}</h4>
                        <p><strong>ID:</strong> {child['child_id']}</p>
                        <p><strong>Age:</strong> {child['age']}</p>
                        <p><strong>Last Interaction:</strong> {child['last_visit']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
