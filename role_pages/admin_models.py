import streamlit as st
import matplotlib.pyplot as plt
import json

def render():
    st.title("🧠 Stuttering Detection Model Evaluation Dashboard")

    # 🔹 Load metrics
    try:
        with open("model_metrics.json", "r") as f:
            metrics = json.load(f)
    except Exception as e:
        st.error(f"Failed to load metrics: {e}")
        return

    # 🔹 Summary Metrics
    st.subheader("📌 Binary Classification Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("F1 Score", metrics["Binary F1 Score"])
    col2.metric("Precision", metrics["Binary Precision"])
    col3.metric("Recall", metrics["Binary Recall"])
    col4.metric("Accuracy", metrics["Binary Accuracy"])

    st.subheader("📌 Sequence-Level Metrics")
    st.metric("Sequence F1 Score", metrics["Sequence F1 Score"])
    st.write(f"Training Epochs: {metrics['Training Epochs']}")

    # 🔹 Class-wise F1 Scores
    st.subheader("📊 Class-wise F1 Scores")
    class_f1 = metrics["Class-wise F1"]
    labels = list(class_f1.keys())
    scores = list(class_f1.values())

    fig1, ax1 = plt.subplots()
    bars = ax1.bar(labels, scores, color="skyblue")
    ax1.set_ylim(0, 1)
    ax1.set_ylabel("F1 Score")
    ax1.set_title("Stutter Type Performance")

    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, height + 0.02, f"{height:.2f}", ha='center', fontsize=10)

    st.pyplot(fig1)

    # 🔹 Loss Curve
    st.subheader("📉 Validation Loss Curve")
    loss_curve = metrics["Loss Curve"]
    fig2, ax2 = plt.subplots()
    ax2.plot(loss_curve, marker='o', color='tomato')
    ax2.set_xlabel("Batch")
    ax2.set_ylabel("Loss")
    ax2.set_title("Loss Over Validation Batches")
    ax2.grid(True)

    st.pyplot(fig2)

    # 🔹 Interpretation
    st.subheader("🧠 Quick Interpretation")
    st.markdown("""
    - **High Binary Recall (0.988)**: Model rarely misses stuttered windows.
    - **Lower WordRep F1 (0.234)**: May need more training data or better feature separation.
    - **Loss curve** shows some spikes — consider smoothing or early stopping.
    """)

# 🔹 Run the dashboard
if __name__ == "__main__":
    render()
