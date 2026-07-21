def parse_topic_label(raw_label: str) -> tuple[str, list[str]]:
    """Parse a BERTopic label like '0_ceasefire_Hamas_negotiations' into a
    display name and keyword list.

    Returns (display_name, keywords).
    """
    parts = raw_label.split("_")
    if parts and parts[0].lstrip("-").isdigit():
        parts = parts[1:]
    display_name = " ".join(w.capitalize() for w in parts) if parts else raw_label
    keywords = parts[:10]
    return display_name, keywords
