from fastai.vision.all import *
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pandas as pd
from pathlib import Path
import librosa
HIDDEN_SIZE = 256
RNN_LAYERS = 2
LOSS_BIN_WEIGHT = 0.2  # ADJUSTED: Decreased from 0.3
LOSS_SEQ_WEIGHT = 0.8  # ADJUSTED: Increased from 0.7
MAX_LEN = 128
WINDOW_SIZE = 64
HOP_SIZE = 16          # ADJUSTED: Decreased from 32 (Increased overlap)
BS = 32
class CNN_BiGRU_StutterTiming(nn.Module):
    def __init__(self, n_types=5, hidden_size=HIDDEN_SIZE, rnn_layers=RNN_LAYERS, sample_shape=(3, WINDOW_SIZE, WINDOW_SIZE)):
        super().__init__()
        self.cnn = nn.Sequential(
            # Block 1: 3 -> 16
            nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.BatchNorm2d(16),
            nn.MaxPool2d((2,1)),
            nn.Dropout(0.3), # ADJUSTED: Increased dropout from 0.2 to 0.3

            # Block 2: 16 -> 32
            nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.BatchNorm2d(32),
            nn.MaxPool2d((2,1)),
            nn.Dropout(0.3), # ADJUSTED: Increased dropout from 0.2 to 0.3

            # Block 3: 32 -> 64
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.BatchNorm2d(64),
            nn.MaxPool2d((2,1)),
            nn.Dropout(0.3), # ADJUSTED: Increased dropout from 0.2 to 0.3
            
            # Block 4: 64 -> 128
            nn.Conv2d(64, 128, 3, padding=1), nn.ReLU(), nn.BatchNorm2d(128),
            nn.AdaptiveAvgPool2d((1, None))
        )

        with torch.no_grad():
            dummy = torch.zeros(1, *sample_shape)
            cnn_out = self.cnn(dummy).squeeze(2)
            cnn_features = cnn_out.shape[1]

        self.rnn_seq = nn.GRU(input_size=cnn_features, hidden_size=hidden_size,
                              num_layers=rnn_layers,
                              batch_first=True, dropout=0.5, bidirectional=True) # ADJUSTED: Increased dropout from 0.3 to 0.5
        
        self.layer_norm = nn.LayerNorm(hidden_size * 2)
        self.fc_bin = nn.Linear(hidden_size * 2, 1)
        self.fc_seq = nn.Linear(hidden_size * 2, n_types)

    def forward(self, x):
        cnn_out = self.cnn(x).squeeze(2)
        x_seq = cnn_out.permute(0, 2, 1) # (B, Time, Features)
        out, _ = self.rnn_seq(x_seq)     # out shape: (B, Time, 2*Hidden)
        out = self.layer_norm(out)
        
        bin_out = self.fc_bin(out[:, -1])
        seq_out = self.fc_seq(out) # (B, Time, n_types)
        
        return bin_out, seq_out

from auth.login_handler import get_user_role, validate_login, register_user
from auth.session_manager import login_user, logout_user

import streamlit as st
from sqlalchemy import create_engine
import os, urllib.parse
from dotenv import load_dotenv
import re

# DB setup
load_dotenv()
db_user = os.getenv("DB_USER")
db_pass = urllib.parse.quote(os.getenv("DB_PASS"))
db_name = os.getenv("DB_NAME")
engine = create_engine(f"mysql+pymysql://{db_user}:{db_pass}@localhost/{db_name}")

# Role-based page map
role_pages = {
    "Admin": {
        "Accounts": "admin_accounts",
        "Models": "admin_models"
    },
    "Therapist": {
        "Home": "therapist_home",
        "Calendar": "therapist_calendar",
        "Child profiles": "therapist_child_profiles"
    },
    "Parent": {
        "Sessions": "parent_sessions"
    }
}

# UI
st.set_page_config(page_title="Stuttering Detection App", layout="centered")

if not st.session_state.get("logged_in"):
    st.title("Stuttering Detection App")

    email = st.text_input("Email")

    if email:
        with engine.begin() as conn:
            role = get_user_role(conn, email)

        if role:
            st.info(f"Account found. Role: {role}")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                with engine.begin() as conn:
                    if validate_login(conn, email, password):
                        login_user(email, role)
                        st.session_state.logged_in = True
                        st.session_state.role = role
                        st.success("Logged in!")
                        st.rerun()  # ← rerun to hide login form
                    else:
                        st.error("Incorrect password.")
        else:
            st.warning("New account will be created.")
            role = st.selectbox("Select role", ("Admin", "Therapist", "Parent"))
            password = st.text_input("Create Password", type="password")
            def is_valid_email(email):
                pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
                return re.match(pattern, email)

            if st.button("Register"):
                if not is_valid_email(email):
                    st.error("❌ Invalid email format. Please enter a valid email address.")
                elif not password:
                    st.error("❌ Password cannot be empty.")
                else:
                    with engine.begin() as conn:
                        register_user(conn, email, password, role)
                        login_user(email, role)
                        st.session_state.logged_in = True
                        st.session_state.role = role
                        st.success("Account created!")
                        st.rerun()


# Role-based navigation
if st.session_state.get("logged_in"):
    role = st.session_state["role"]
    page_options = list(role_pages[role].keys())
    selected_page = st.sidebar.radio("Navigation", page_options)

    if st.sidebar.button("Logout"):
        logout_user()
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    module_name = role_pages[role][selected_page]
    module = __import__(f"role_pages.{module_name}", fromlist=["render"])
    module.render()