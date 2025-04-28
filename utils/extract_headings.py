import pdfplumber
from collections import defaultdict
from .validate_headings import is_valid_heading
# import json

line_tolerance = 3


def extract_headings(pdf_path):
    headings = {}  # { page_num: { "page_title": ..., "headlines": [...] } }

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):  # Track page number
            page_headlines = []  # List for current page's headlines
            page_title = ""  # Placeholder for page's title

            word_objects = page.extract_words(extra_attrs=["fontname", "size"],
                                              keep_blank_chars=False,
                                              use_text_flow=True)

            # Skip pages with no text
            if not word_objects:
                headings[page_num] = {"page_title": "", "headlines": []}
                continue

            # === Detect page title ===
            top_words = [
                w for w in word_objects if w['top'] < 0.05 * page.height
            ]
            top_words.sort(key=lambda w: w['size'], reverse=True)
            if top_words and top_words[0] and top_words[0]["text"]:
                page_title = top_words[0]["text"]

            # === Normal headline extraction ===
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
                sentence_parts = []
                word_groups = final_groups[font_key]

                # Combine ALL words across ALL groups for this font_key
                for group in word_groups:
                    for word in group:
                        sentence_parts.append(word["text"])

                if sentence_parts:
                    sentence = " ".join(sentence_parts)
                    if is_valid_heading(sentence):
                        page_headlines.append(sentence)

            # Save both page title and headlines
            headings[page_num] = {
                "page_title": page_title.strip(),
                "headlines": page_headlines
            }

    return headings
