def normalize_text(s: str) -> str:
    return s.replace("Ё", "Е").replace("ё", "е").lower().strip()
