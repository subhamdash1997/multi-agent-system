import json
from pathlib import Path
from typing import Any

from utils.country_utils import COUNTRY_ALIAS, clean_text, country_name_to_code


DATA_DIR = Path(__file__).resolve().parent

with (DATA_DIR / "country_main_airports.json").open(encoding="utf-8") as file:
    COUNTRY_MAIN_AIRPORTS = json.load(file)


def airport_country_matches(airport: dict[str, Any], country_code: str) -> bool:
    airport_country = airport.get("country")
    if not isinstance(airport_country, str) or not isinstance(country_code, str):
        return False

    return airport_country.strip().upper() == country_code.strip().upper()


def airpot_country_matches(airport: dict[str, Any], country_code: str) -> bool:
    """Backward-compatible alias for the misspelled public function."""
    return airport_country_matches(airport, country_code)


def get_best_airport_for_country(country_code: str) -> str | None:
    if not isinstance(country_code, str):
        return None

    normalized_code = clean_text(country_code).upper()
    for country_name, aliases in COUNTRY_ALIAS.items():
        country_values = [country_name, *aliases]
        if any(clean_text(value).upper() == normalized_code for value in country_values):
            airport = COUNTRY_MAIN_AIRPORTS.get(country_name)
            return airport.get("airport") if airport else None

        if country_name_to_code(country_name) == normalized_code:
            airport = COUNTRY_MAIN_AIRPORTS.get(country_name)
            return airport.get("airport") if airport else None

    return None
