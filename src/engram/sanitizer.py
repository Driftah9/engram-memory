"""FTS5 query sanitizer — strips operator characters from user input."""

# Character translation table for FTS5 operator removal
_FTS_SPECIAL = str.maketrans({
    "'": "",   # apostrophe breaks tokenizer
    '"': "",   # quote delimiter — strip bare, use phrase() for phrases
    "-": " ",  # treated as NOT operator at word boundaries
    "*": "",   # prefix wildcard — strip unless caller explicitly passes it
    "^": "",   # boost operator
    ":": " ",  # field prefix syntax
    "(": "",
    ")": "",
})


def sanitize_fts(term: str) -> str:
    """Strip FTS5 operator characters from a raw user term before MATCH.

    FTS5 interprets certain characters as query operators. This function removes
    them so that user input is treated as literal search terms.

    Args:
        term: Raw user input (may contain operators, apostrophes, etc.)

    Returns:
        Cleaned term safe for FTS5 MATCH clause.
        Returns empty string if nothing remains after cleaning.

    Examples:
        >>> sanitize_fts("can't")
        'cant'
        >>> sanitize_fts("home-buyer")
        'home buyer'
        >>> sanitize_fts("(advanced) tips*")
        'advanced tips'
    """
    cleaned = term.translate(_FTS_SPECIAL).strip()
    # Collapse multiple spaces
    return " ".join(cleaned.split())
