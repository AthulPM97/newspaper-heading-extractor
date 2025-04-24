import streamlit as st
import pdfplumber
from collections import defaultdict
import json

# --- Helper Functions ---
line_tolerance = 3


def is_valid_heading(text):
    """Check if a heading is meaningful"""
    # Conditions for invalid headings
    if not text.strip():
        return False
    if len(text.split()) <= 1:  # Single word or character repeats
        return False
    if text.isnumeric() or all(word.isnumeric() for word in text.split()):
        return False
    if len(text) < 5:  # Very short text
        return False
    if text.lower() in ['p1 p1', 'u u']:  # Specific blacklist
        return False
    return True


def extract_headings(pdf_path):
    headings = {}  # Dictionary to store headings by page number

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):  # Track page number
            page_headings = []  # Initialize list for current page's headings

            word_objects = page.extract_words(extra_attrs=["fontname", "size"],
                                              keep_blank_chars=False,
                                              use_text_flow=True)

            # Skip pages with no text
            if not word_objects:
                headings[page_num] = []  # Add empty list for empty page
                continue

            # Extract all unique heights (using a set to avoid duplicates)
            unique_font_sizes = {word["size"] for word in word_objects}

            # Sort in descending order and take the top 6
            top_font_sizes = sorted(unique_font_sizes, reverse=True)[:6]

            # Group words by (fontname, size)
            font_size_groups = defaultdict(list)

            for word in word_objects:
                size = word["size"]
                fontname = word["fontname"]

                if size in top_font_sizes:
                    font_size_groups[(fontname, size)].append(word)

            # Further group by proximity in lines (same or adjacent top/bottom)
            final_groups = defaultdict(list)

            for (fontname, size), words in font_size_groups.items():
                # Sort words by vertical position (top)
                words_sorted = sorted(words, key=lambda x: x["top"])

                i = 0
                n = len(words_sorted)

                while i < n:
                    current_word = words_sorted[i]
                    current_top = current_word["top"]
                    current_bottom = current_word["bottom"]

                    # Find words in the same or nearby lines
                    group = [current_word]

                    j = i + 1
                    while j < n:
                        next_word = words_sorted[j]
                        next_top = next_word["top"]

                        # Check if next word is within `line_tolerance` lines
                        if (abs(next_top - current_top) <= line_tolerance *
                            (current_bottom - current_top)):
                            group.append(next_word)
                            j += 1
                        else:
                            break

                    final_groups[(fontname, size)].append(group)
                    i = j  # Move to next ungrouped word

            # Process groups for this page
            for font_key in final_groups:
                sentence_parts = []  # Reset for each font_key
                word_groups = final_groups[font_key]

                # Combine ALL words across ALL groups for this font_key
                for group in word_groups:
                    for word in group:
                        sentence_parts.append(word["text"])

                # Join all words into a single sentence per font_key
                if sentence_parts:  # Ensure non-empty
                    sentence = " ".join(sentence_parts)
                    if is_valid_heading(sentence):
                        page_headings.append(sentence)

            # Add page's headings to the dictionary
            headings[page_num] = page_headings

    return headings


# --- Streamlit UI ---
st.set_page_config(page_title="PDF Article Extractor", layout="wide")
st.title("📰 Newspaper PDF Article Extractor")

uploaded_file = st.file_uploader("Upload a newspaper-style PDF", type="pdf")

if uploaded_file:
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

    # Add download button
    st.download_button(label="Download as JSON",
                       data=json_data,
                       file_name="articles.json",
                       mime="application/json")
