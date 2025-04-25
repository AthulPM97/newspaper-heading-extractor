import pdfplumber
from collections import defaultdict
from .validate_headings import is_valid_heading

line_tolerance = 3


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
