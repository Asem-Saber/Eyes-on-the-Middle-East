import os
import json

PROCESSED_PATH = r"F:\Career\Projects\aljazeera-dashboard\news\processed_articles.json"

def load_data():
    """
    Loads processed articles from the JSON file.
    This acts as a temporary data layer until the database is fully implemented.
    """
    if os.path.exists(PROCESSED_PATH):
        with open(PROCESSED_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
