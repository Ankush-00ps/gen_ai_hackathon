import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import matplotlib.pyplot as plt
import re
from typing import List, Tuple
from collections import Counter

# ---------------------------
# Page Setup
# ---------------------------
st.set_page_config(page_title="Legal Document Analyzer", page_icon="📄", layout="wide")

st.markdown("""
    <style>
      .header { text-align: center; color: #1F618D; font-weight: 700; }
      .subtitle { text-align:center; color: #34495E; margin-bottom: 20px; }
      .card { background: #F8F9F9; padding: 14px; border-radius: 8px; }
      .small { font-size: 0.9rem; color: #6C757D; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='header'>📄 Legal Document Analyzer</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Summarize, extract named entities, and analyze risk</div>", unsafe_allow_html=True)

# ---------------------------
# Helper Functions
# ---------------------------
def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, List[Image.Image]]:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        st.error(f"Could not open PDF: {e}")
        return "", []
    texts = []
    page_images = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            texts.append(text)
        else:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_images.append(img)
    return "\n\n".join(texts).strip(), page_images

def fake_summarize(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:2]) if sentences else text[:500]

def fake_ner(text: str):
    words = re.findall(r'\b[A-Z][a-zA-Z&]+\b(?:\s+\b[A-Z][a-zA-Z&]+\b)*', text)
    return [{"label": "ORG/NAME", "text": w} for w in set(words[:15])]

def analyze_risk(text: str):
    RISK_KEYWORDS = [
        "liability", "termination", "penalty", "indemnify", "fine", "breach",
        "damages", "warranty", "limitation", "dispute", "arbitration", "confidentiality"
    ]
    text_lower = text.lower()
    keyword_counts = {kw: text_lower.count(kw) for kw in RISK_KEYWORDS}
    total_risk_hits = sum(keyword_counts.values())
    total_words = max(1, len(text_lower.split()))
    risk_score = total_risk_hits / total_words * 1000
    return keyword_counts, total_risk_hits, total_words, risk_score

# ---------------------------
# Sidebar Controls
# ---------------------------
st.sidebar.title("Upload & Settings")
uploaded_file = st.sidebar.file_uploader("Upload a legal PDF", type=["pdf"])
run_button = st.sidebar.button("Process Document")

# ---------------------------
# Main UI Layout
# ---------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Document")
    if uploaded_file:
        st.markdown(f"**Filename:** {uploaded_file.name}")
        bytes_data = uploaded_file.read()
        extracted_text, page_images = extract_text_from_pdf(bytes_data)
        st.text_area("Extracted text (preview)", extracted_text[:5000], height=300)
    else:
        st.info("Upload a PDF from the sidebar and click 'Process Document'.")

with col2:
    st.markdown("### Controls")
    st.markdown("<div class='card small'>Upload a PDF and click Process to run analysis.</div>", unsafe_allow_html=True)
    if st.button("Clear / Reset"):
        st.experimental_rerun()

# ---------------------------
# Processing and Results
# ---------------------------
if run_button and uploaded_file:
    with st.spinner("Running analysis..."):
        summary_text = fake_summarize(extracted_text)
        entities = fake_ner(extracted_text)
        keyword_counts, total_risk_hits, total_words, risk_score = analyze_risk(extracted_text)

    st.markdown("---")
    st.markdown("## Results")

    col_main, col_entities, col_graphs = st.columns([2, 1, 1])

    with col_main:
        st.markdown("### Summary")
        st.write(summary_text)
        st.download_button("Download Summary (txt)", summary_text, file_name="summary.txt")

    with col_entities:
        st.markdown("### Named Entities")
        for ent in entities:
            st.markdown(f"- **{ent['label']}** — {ent['text']}")
        st.download_button("Download Entities (txt)", "\n".join(f"{e['label']}: {e['text']}" for e in entities), file_name="entities.txt")

    with col_graphs:
        st.markdown("### Risk Analysis")
        labels = ["Risk Mentions", "Other Words"]
        sizes = [total_risk_hits, total_words - total_risk_hits]
        colors = ["#E74C3C", "#3498DB"]
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, colors=colors)
        ax1.set_title(f"Risk Overview\nScore: {risk_score:.2f}")
        st.pyplot(fig1)

        top_k = 6
        counter = Counter(keyword_counts)
        most_common = counter.most_common(top_k)
        if most_common:
            keys, vals = zip(*most_common)
            fig2, ax2 = plt.subplots()
            ax2.barh(keys, vals, color="#E67E22")
            ax2.set_xlabel("Mentions")
            ax2.set_title("Top Risk Keywords")
            ax2.invert_yaxis()
            st.pyplot(fig2)
        else:
            st.info("No risk-related keywords detected.")

    st.markdown("---")
    st.markdown("### Send Results")
    email = st.text_input("Enter email to send results (optional)")
    if st.button("Send Email"):
        if not email or "@" not in email:
            st.error("Enter a valid email address.")
        else:
            st.success(f"Pretend-sent results to {email} (SMTP not implemented).")

st.markdown("---")
st.markdown("<div class='small'>Tip: Risk analysis is based on keyword frequency. For deeper insights, integrate clause classification.</div>", unsafe_allow_html=True)