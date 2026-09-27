import json
import re
from pathlib import Path

import pycountry


DATA_DIR = Path(__file__).resolve().parent

with (DATA_DIR / "country_alias.json").open(encoding="utf-8") as file:
    COUNTRY_ALIAS = json.load(file)


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    stop_words = {
        "flight", "flights", "ticket", "tickets", "trip", "travel",
        "plan", "complete", "days", "day", "including", "hotel",
        "hotels", "sightseeing", "under", "budget", "info", "information", "to",
    }
    return " ".join(word for word in text.split() if word not in stop_words)


def country_name_to_code(text: str) -> str | None:
    normalized_text = clean_text(text)

    for country_name, aliases in COUNTRY_ALIAS.items():
        normalized_aliases = {clean_text(alias) for alias in aliases}
        if normalized_text == clean_text(country_name) or normalized_text in normalized_aliases:
            country = pycountry.countries.get(name=country_name)
            if country is not None:
                return country.alpha_2

    try:
        return pycountry.countries.lookup(normalized_text).alpha_2
    except LookupError:
        return None
