import unicodedata


def normalize_key(label):
    r"""Apply Unicode NFKC, then casefold; trim and collapse Unicode whitespace to '-'.

    Raise ValueError when the resulting key is empty.

    >>> normalize_key("Alpha\tBeta") == normalize_key("alpha beta") == "alpha-beta"
    True
    >>> normalize_key(" \uff21lpha\u00a0\u2003Beta\n")
    'alpha-beta'
    >>> normalize_key("Stra\u00dfe")
    'strasse'
    >>> normalize_key("alpha_beta")
    'alpha_beta'
    >>> normalize_key("-")
    '-'
    >>> normalize_key("")
    Traceback (most recent call last):
        ...
    ValueError: empty label
    >>> normalize_key(" \t\u2003\n")
    Traceback (most recent call last):
        ...
    ValueError: empty label
    """
    key = "-".join(unicodedata.normalize("NFKC", label).casefold().split())
    if not key:
        raise ValueError("empty label")
    return key


def preview_key(label):
    return normalize_key(label)


def import_label(label, seen):
    r"""Import a label without rewriting existing keys.

    >>> seen = {"Legacy Key"}
    >>> key = import_label("Alpha\tBeta", seen)
    >>> key == preview_key("alpha beta") == "alpha-beta"
    True
    >>> seen == {"Legacy Key", "alpha-beta"}
    True
    >>> import_label("alpha beta", seen)
    Traceback (most recent call last):
        ...
    ValueError: duplicate label
    >>> seen == {"Legacy Key", "alpha-beta"}
    True
    >>> import_label(" \u2003\t", seen)
    Traceback (most recent call last):
        ...
    ValueError: empty label
    >>> seen == {"Legacy Key", "alpha-beta"}
    True
    >>> import_label("Gamma", seen)
    'gamma'
    >>> seen == {"Legacy Key", "alpha-beta", "gamma"}
    True
    """
    key = normalize_key(label)
    if key in seen:
        raise ValueError("duplicate label")
    seen.add(key)
    return key
