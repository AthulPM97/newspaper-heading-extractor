import streamlit as st
import json
from mongo import client
from datetime import datetime, timezone

from utils import extract_headings

# --- Database ---
db = client["headlines"]
collection = db["newspaper_data"]

# --- Streamlit UI ---
st.set_page_config(page_title="PDF Article Extractor", layout="wide")
st.title("📰 Newspaper PDF Article Extractor")

uploaded_file = st.file_uploader("Upload a newspaper-style PDF (works with Hindu and Mint)", type="pdf")

if uploaded_file:
    filename = uploaded_file.name
    with st.spinner("Extracting articles..."):
        articles = extract_headings(uploaded_file)

    st.success(f"Found headings on {len(articles)} pages")

    # Display headings by page in the Streamlit UI
    for page_num, page_headings in articles.items():
        if page_headings:  # Only show pages with headings
            st.subheader(f"Page {page_num + 1} Headings:"
                         )  # +1 for human-readable numbering
            for i, heading in enumerate(page_headings, start=1):
                st.write(f"{i}. {heading}")

    # Optional: Show raw data in expander
    with st.expander("Show raw extracted data"):
        st.write(articles)

    # Convert to JSON string
    json_data = json.dumps(articles, indent=2)
    
    # Convert list to dict with string keys to satisfy mongodb :)
    headlines_dict = {str(i): articles[i] for i, article in enumerate(articles)}
    doc = {
        "articles": headlines_dict,
        "source": "streamlit_app",
        "filename": filename,
        "timestamp": datetime.now(timezone.utc)
    }
    # Check for duplicate filename before insertion
    if collection.find_one({"filename": filename}):
        st.warning(f"Document with filename '{filename}' already exists in the database.")
    else:
        result = collection.insert_one(doc)
        st.success(f"Inserted document with ID: {result.inserted_id}")

    # Add download button
    st.download_button(label="Download as JSON",
                       data=json_data,
                       file_name="articles.json",
                       mime="application/json")
