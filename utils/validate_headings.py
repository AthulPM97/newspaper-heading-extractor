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
