import os
import fitz  # PyMuPDF
import docx
from PIL import Image
import pytesseract
import warnings

from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForTokenClassification

warnings.filterwarnings("ignore")

# ---------- TEXT EXTRACTION ----------
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        page_text = page.get_text()
        if not page_text.strip():
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(img)
        text += page_text + "\n"
    return text

def extract_text_from_docx(docx_path):
    doc = docx.Document(docx_path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_txt(txt_path):
    with open(txt_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text_from_image(img_path):
    image = Image.open(img_path)
    return pytesseract.image_to_string(image)

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    elif ext == ".txt":
        return extract_text_from_txt(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

# ---------- CHUNKING ----------
def chunk_text(text, chunk_size=1000, overlap=200):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

# ---------- GENERATIVE SUMMARIZATION ----------
# Initialize generative model
summ_model_name = "facebook/bart-large-cnn"
summ_tokenizer = AutoTokenizer.from_pretrained(summ_model_name)
summ_model = AutoModelForSeq2SeqLM.from_pretrained(summ_model_name)
summarizer = pipeline("summarization", model=summ_model, tokenizer=summ_tokenizer)

def summarize_large_text(text, max_chunk_words=1000):
    chunks = chunk_text(text, chunk_size=max_chunk_words)
    summaries = []
    for chunk in chunks:
        try:
            summary = summarizer(chunk, max_length=250, min_length=100, do_sample=False)[0]['summary_text']
            summaries.append(summary)
        except:
            continue
    combined = " ".join(summaries)
    # recursive summarization for very long text
    if len(combined.split()) > max_chunk_words:
        return summarize_large_text(combined, max_chunk_words)
    return combined

# ---------- LEGAL-SPECIFIC NER ----------
ner_model_name = "nlpaueb/legal-bert-base-uncased"
ner_tokenizer = AutoTokenizer.from_pretrained(ner_model_name)
ner_model = AutoModelForTokenClassification.from_pretrained(ner_model_name)
ner_pipeline = pipeline("ner", model=ner_model, tokenizer=ner_tokenizer)

def extract_legal_entities(text, chunk_size=500):
    chunks = chunk_text(text, chunk_size)
    entities = {}
    for chunk in chunks:
        results = ner_pipeline(chunk)
        for r in results:
            ent_type = r['entity']
            ent_val = r['word'].replace('##', '')
            if ent_type not in entities:
                entities[ent_type] = set()
            entities[ent_type].add(ent_val)
    # Clean up duplicates and junk characters
    for k in entities:
        entities[k] = set([v.strip(" ,.'") for v in entities[k] if v.strip()])
    return entities

# ---------- MAIN PIPELINE ----------
def process_legal_document(file_path):
    text = extract_text(file_path)
    summary = summarize_large_text(text)
    entities = extract_legal_entities(text)

    output_folder = "legal_document_analysis"
    os.makedirs(output_folder, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_folder, f"{base_name}_analysis.txt")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("Summary:\n")
        f.write(summary + "\n\nNamed Entities:\n")
        for etype, evalues in entities.items():
            f.write(f"{etype}: {', '.join(evalues)}\n")
    return output_file

# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    file_path = input("Enter the path to the legal file (PDF, DOCX, TXT, Image): ")
    output_file = process_legal_document(file_path)
    print(f"Analysis results saved at: {os.path.abspath(output_file)}")

