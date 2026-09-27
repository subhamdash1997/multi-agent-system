import json
import os
import re
import certifi
import airportsdata
from pathlib import Path
import requests

from dotenv import load_dotenv
from utils.airport_utils import (
    airpot_country_matches,
    get_best_airport_for_country,
)
from utils.country_utils import COUNTRY_ALIAS, clean_text, country_name_to_code


load_dotenv()

os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_DATA", "IND")

BASE_URL = "https://api.aviationstack.com/v1/flights"

AIRPORTS = airportsdata.load("IATA")



DATA_DIR = Path(__file__).resolve().parent.parent / "utils"


def _load_json(file_name: str):
    with (DATA_DIR / file_name).open(encoding="utf-8") as file:
        return json.load(file)


COUNTRY_MAIN_AIRPORTS = _load_json("country_main_airports.json")
CITY_MAIN_AIRPORTS = _load_json("city_main_airports.json")


def find_location_mentions(query: str) -> list[str]:
    """Find known country and city names in a natural-language query."""
    if not isinstance(query, str):
        return []

    normalized_query = clean_text(query)
    mentions = []

    location_names = [
        alias
        for aliases in COUNTRY_ALIAS.values()
        for alias in aliases
    ]
    location_names.extend(COUNTRY_ALIAS.keys())
    location_names.extend(CITY_MAIN_AIRPORTS.keys())

    for location in sorted(set(location_names), key=len, reverse=True):
        normalized_location = clean_text(location)
        if re.search(rf"\b{re.escape(normalized_location)}\b", normalized_query):
            mentions.append(location)

    return list(dict.fromkeys(mentions))


def resolve_location_to_iata(location: str) -> str | None:
    """Resolve a city, country, alias, or IATA code to an airport code."""
    if not isinstance(location, str):
        return None

    normalized_location = clean_text(location)
    if not normalized_location:
        return None

    airport_code = normalized_location.upper()
    if airport_code in AIRPORTS:
        return airport_code

    for city_name, city_data in CITY_MAIN_AIRPORTS.items():
        if clean_text(city_name) == normalized_location:
            airports = city_data.get("airports", [])
            return airports[0].get("code") if airports else None

    country_code = country_name_to_code(normalized_location)
    if country_code:
        return get_best_airport_for_country(country_code)

    return None


def parse_route(query: str):
    """
    Returns:
    dep_iata, arr_iata

    Can return:
    None, None  -> global live flights
    DAC, NRT    -> filtered route
    DAC, None   -> all flights from DAC
    None, NRT   -> all flights to NRT
    """

    if not isinstance(query, str):
        return None, None

    q = query.strip()
    if not q:
        return None, None

    q_lower = q.lower()

    # Global / all-country query
    global_keywords = [
        "all country",
        "all countries",
        "global flight",
        "global flights",
        "all flight",
        "all flights",
        "worldwide flight",
        "worldwide flights",
    ]

    if any(keyword in q_lower for keyword in global_keywords):
        return None, None

    # Direct IATA code route: DAC to NRT
    codes = re.findall(r"\b[A-Za-z]{3}\b", q)

    if len(codes) >= 2:
        dep = codes[0].upper()
        arr = codes[1].upper()
        return dep, arr

    # Pattern: from X to Y
    match = re.search(
        r"\bfrom\s+(.+?)\s+\bto\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )

    if match:
        origin_text = match.group(1)
        dest_text = match.group(2)

        dep_iata = resolve_location_to_iata(origin_text)
        arr_iata = resolve_location_to_iata(dest_text)

        return dep_iata, arr_iata

    # Pattern: to Y from X
    match = re.search(
        r"\bto\s+(.+?)\s+\bfrom\s+(.+?)(?:\s+(?:on|for|under|including|with|in|at)\b|[.!?]|$)",
        q_lower,
    )

    if match:
        dest_text = match.group(1)
        origin_text = match.group(2)

        dep_iata = resolve_location_to_iata(origin_text)
        arr_iata = resolve_location_to_iata(dest_text)

        return dep_iata, arr_iata

    # Pattern: destination trip from origin
    match = re.search(
        r"\b(?:trip|travel|holiday)\b.*?\bfrom\s+(.+?)(?:[.!?]|$)",
        q_lower,
    )

    if match:
        origin_text = match.group(1)
        dep_iata = resolve_location_to_iata(origin_text)
        mentions = find_location_mentions(q)
        destinations = [
            mention for mention in mentions
            if clean_text(mention) != clean_text(origin_text)
        ]
        arr_iata = resolve_location_to_iata(destinations[0]) if destinations else None
        return dep_iata, arr_iata

    # Pattern: flights from X
    match = re.search(r"\bfrom\s+(.+?)(?:[.!?]|$)", q_lower)

    if match:
        origin_text = match.group(1)
        dep_iata = resolve_location_to_iata(origin_text)
        return dep_iata, None

    # Pattern: flights to X
    match = re.search(r"\bto\s+(.+?)(?:[.!?]|$)", q_lower)

    if match:
        dest_text = match.group(1)
        arr_iata = resolve_location_to_iata(dest_text)
        return None, arr_iata

    # Fallback: find country/city mentions
    mentions = find_location_mentions(q)

    if len(mentions) >= 2:
        dep_iata = resolve_location_to_iata(mentions[0])
        arr_iata = resolve_location_to_iata(mentions[1])
        return dep_iata, arr_iata

    if len(mentions) == 1:
        arr_iata = resolve_location_to_iata(mentions[0])
        return DEFAULT_ORIGIN_IATA, arr_iata

    return None, None


def format_flight(flight: dict):
    airline = flight.get("airline", {}).get("name") or "Unknown airline"
    flight_number = flight.get("flight", {}).get("iata") or "Unknown flight number"
    status = flight.get("flight_status") or "Unknown"

    dep = flight.get("departure", {}) or {}
    arr = flight.get("arrival", {}) or {}

    dep_airport = dep.get("airport") or "Unknown departure airport"
    dep_iata = dep.get("iata") or "Unknown"
    dep_terminal = dep.get("terminal") or "N/A"
    dep_gate = dep.get("gate") or "N/A"
    dep_scheduled = dep.get("scheduled") or "Unknown"
    dep_delay = dep.get("delay")
    dep_delay_text = f"{dep_delay} minutes" if dep_delay is not None else "N/A"

    arr_airport = arr.get("airport") or "Unknown arrival airport"
    arr_iata = arr.get("iata") or "Unknown"
    arr_terminal = arr.get("terminal") or "N/A"
    arr_gate = arr.get("gate") or "N/A"
    arr_scheduled = arr.get("scheduled") or "Unknown"
    arr_delay = arr.get("delay")
    arr_delay_text = f"{arr_delay} minutes" if arr_delay is not None else "N/A"

    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {dep_airport}
- IATA: {dep_iata}
- Terminal: {dep_terminal}
- Gate: {dep_gate}
- Scheduled: {dep_scheduled}
- Delay: {dep_delay_text}

Arrival:
- Airport: {arr_airport}
- IATA: {arr_iata}
- Terminal: {arr_terminal}
- Gate: {arr_gate}
- Scheduled: {arr_scheduled}
- Delay: {arr_delay_text}
""".strip()


def search_flights(query: str, limit: int = 10):
    if not API_KEY:
        return (
            "Flight API error: AVIATIONSTACK_API_KEY is missing.\n"
            "Please add this in your .env file:\n"
            "AVIATIONSTACK_API_KEY=your_api_key_here"
        )

    dep_iata, arr_iata = parse_route(query)

    params = {
        "access_key": API_KEY,
        "limit": min(limit, 100),
    }

    if dep_iata:
        params["dep_iata"] = dep_iata

    if arr_iata:
        params["arr_iata"] = arr_iata

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Flight API request failed: {e}"
    except ValueError:
        return "Flight API returned invalid JSON."

    if "error" in data:
        error = data["error"]
        return (
            "Flight API error:\n"
            f"Code: {error.get('code', 'Unknown')}\n"
            f"Message: {error.get('message', 'Unknown error')}"
        )

    flight_data = data.get("data", [])

    if not flight_data:
        route_text = ""

        if dep_iata and arr_iata:
            route_text = f" for route {dep_iata} to {arr_iata}"
        elif dep_iata:
            route_text = f" from {dep_iata}"
        elif arr_iata:
            route_text = f" to {arr_iata}"

        return (
            f"No live flight data found{route_text}.\n\n"
            "Note: AviationStack provides live/status flight data, not ticket prices. "
            "For actual fare prices, use a flight-pricing API such as Amadeus."
        )

    route_info = "Global live flights"

    if dep_iata and arr_iata:
        route_info = f"Live flights from {dep_iata} to {arr_iata}"
    elif dep_iata:
        route_info = f"Live flights from {dep_iata}"
    elif arr_iata:
        route_info = f"Live flights to {arr_iata}"

    formatted_flights = [format_flight(flight) for flight in flight_data[:limit]]

    return f"{route_info}\n\n" + "\n\n---\n\n".join(formatted_flights)


if __name__ == "__main__":
    print(search_flights("Plan a 7 days Japan trip from India"))
    print("\n" + "=" * 80 + "\n")
    print(search_flights("all country flight info"))
