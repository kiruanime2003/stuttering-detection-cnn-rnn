import streamlit as st
import torch
import numpy as np
import librosa
from pydub import AudioSegment
import os
import whisper
from fpdf import FPDF

from model import CNN_BiGRU_StutterTiming  # Your trained model class

# 🔹 Constants
WINDOW_SIZE = 64
FRAME_DURATION = 0.02
THRESHOLD = 0.5
TYPE_NAMES = ["Prolongation", "Block", "SoundRep", "WordRep", "Interjection"]

# 🔹 Load model
@st.cache_resource
def load_model():
    model = CNN_BiGRU_StutterTiming(sample_shape=(3, 64, WINDOW_SIZE))
    state_dict = torch.load("stutter_model_full.pt", map_location=torch.device('cpu'))
    model.load_state_dict(state_dict)
    model.eval()
    return model

model = load_model()

# 🔹 Load Whisper
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

whisper_model = load_whisper()

# 🔹 Save uploaded file
def save_uploaded_file(uploaded_file, temp_dir="temp_audio"):
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# 🔹 Convert to WAV if needed
def convert_to_wav(file_path):
    if file_path.lower().endswith(".wav"):
        return file_path
    audio = AudioSegment.from_file(file_path)
    wav_path = os.path.splitext(file_path)[0] + ".wav"
    audio.export(wav_path, format="wav")
    return wav_path

# 🔹 Preprocess audio for model
def preprocess_audio(file_path, sr=16000, n_mels=64, max_len=128):
    y, _ = librosa.load(file_path, sr=sr)
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels)
    S_db = librosa.power_to_db(S, ref=np.max)

    if S_db.shape[1] < max_len:
        S_db = np.pad(S_db, ((0, 0), (0, max_len - S_db.shape[1])), mode='constant')
    else:
        S_db = S_db[:, :max_len]

    delta = librosa.feature.delta(S_db)
    delta2 = librosa.feature.delta(S_db, order=2)

    for arr in [S_db, delta, delta2]:
        arr -= np.mean(arr)
        arr /= np.std(arr)

    stacked = np.stack([S_db, delta, delta2], axis=0)
    return torch.tensor(stacked, dtype=torch.float32).unsqueeze(0)

# 🔹 Group stutter events
def group_stutter_events(seq_probs, threshold=THRESHOLD, frame_duration=FRAME_DURATION):
    seq_probs = seq_probs.T
    events = []
    type_counts = [0] * len(TYPE_NAMES)

    for type_idx, st_type in enumerate(TYPE_NAMES):
        active = False
        start_frame = None
        for t in range(seq_probs.shape[1]):
            prob = seq_probs[type_idx, t]
            if prob > threshold:
                if not active:
                    active = True
                    start_frame = t
            else:
                if active:
                    end_frame = t
                    start = round(start_frame * frame_duration, 2)
                    end = round(end_frame * frame_duration, 2)
                    events.append((st_type, start, end))
                    type_counts[type_idx] += 1
                    active = False
        if active:
            end_frame = seq_probs.shape[1]
            start = round(start_frame * frame_duration, 2)
            end = round(end_frame * frame_duration, 2)
            events.append((st_type, start, end))
            type_counts[type_idx] += 1

    return events, dict(zip(TYPE_NAMES, type_counts))

# 🔹 Transcribe audio
def transcribe_audio(wav_path):
    result = whisper_model.transcribe(wav_path)
    return result["text"], result["segments"]

# 🔹 Export transcript to PDF
def export_transcript_to_pdf(transcript_text, filename="transcript.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in transcript_text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

# 🔹 Streamlit UI
def render():
    st.title("Stuttering Detection and Transcript Generator")
    uploaded_file = st.file_uploader("Upload an audio file (.wav, .mp3, .m4a)", type=["wav", "mp3", "m4a"])

    if st.button("Predict", type="primary") and uploaded_file:
        try:
            raw_path = save_uploaded_file(uploaded_file)
            wav_path = convert_to_wav(raw_path)

            # 🔹 Transcription
            transcript_text, segments = transcribe_audio(wav_path)
            st.subheader("📝 Transcript")
            st.text_area("Full Transcript", transcript_text, height=200)

            # 🔹 PDF Download
            pdf_path = export_transcript_to_pdf(transcript_text)
            with open(pdf_path, "rb") as f:
                st.download_button("Download Transcript as PDF", f, file_name="transcript.pdf")

            # 🔹 Stutter Prediction
            x = preprocess_audio(wav_path)
            with torch.no_grad():
                bin_pred, seq_pred = model(x)
                bin_prob = torch.sigmoid(bin_pred).item()
                seq_probs = torch.sigmoid(seq_pred).squeeze(0).numpy()

            st.subheader("Prediction Result")
            if bin_prob > 0.5:
                st.success(f"🧠 Stutter Detected\n\nBinary stutter probability: {bin_prob:.3f}")
            else:
                st.info(f"✅ No Stutter Detected\n\nBinary stutter probability: {bin_prob:.3f}")

            st.subheader("📍 Detected Stutter Events with Transcript")
            events, type_counts = group_stutter_events(seq_probs)
            if events:
                for st_type, start, end in events:
                    st.write(f"🕒 {start:.2f}s – {end:.2f}s → {st_type}")
                    matching_lines = [seg["text"] for seg in segments if seg["start"] >= start and seg["end"] <= end]
                    for line in matching_lines:
                        st.markdown(f"> {line}")
            else:
                st.write("⚠️ Stuttering detected, but no confident events found.")

            st.subheader("📊 Total Stutter Type Counts")
            for t in TYPE_NAMES:
                st.write(f"{t}: {type_counts[t]}")

        except Exception as e:
            st.error(f"❌ Error during prediction: {e}")

# 🔹 Run the app
if __name__ == "__main__":
    render()
