import unicodedata


def normalize_key(label):
    """Apply Unicode NFKC, then casefold; trim and collapse Unicode whitespace to '-'.

    Raise ValueError when the resulting key is empty.
    """
    key = "-".join(unicodedata.normalize("NFKC", label).casefold().split())
    if not key:
        raise ValueError("empty label")
    return key


def preview_key(label):
    return normalize_key(label)


def import_label(label, seen):
    key = normalize_key(label)
    if key in seen:
        raise ValueError("duplicate label")
    seen.add(key)
    return key
