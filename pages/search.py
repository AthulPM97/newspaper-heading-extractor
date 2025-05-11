import streamlit as st
from datetime import datetime
from mongo import client

# --- Database ---
db = client["headlines"]
collection = db["newspaper_data"]

# def render():
st.title("🔎 Search Headlines")

keyword = st.text_input("Enter a keyword to search for")

if keyword:
    # Fetch all documents since we need to manually search nested fields
    results = collection.find()
    found_any = False

    for doc in results:
        matched_headlines = []

        for page, headlines in doc.get("articles", {}).items():
            for headline in headlines:
                if keyword.lower() in headline.lower():
                    matched_headlines.append(f"Page {page}: {headline}")

        if matched_headlines:
            found_any = True
            st.subheader(doc.get("filename", "Unknown File"))
            timestamp = doc.get("timestamp")
            if timestamp:
                date_str = timestamp.strftime("%B %d, %Y")  # e.g. "April 25, 2025"
                st.caption(f"Date: {date_str}")

            for line in matched_headlines:
                st.markdown(f"- {line}")
            st.markdown("---")

    if not found_any:
        st.info("No matching headlines found.")
