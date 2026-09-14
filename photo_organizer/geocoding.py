import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Tuple

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "TensorChronicle-PhotoOrganizer/1.0"


def geocode_place(query: str) -> Optional[Tuple[float, float, str]]:
    """Zamienia nazwę miejsca na współrzędne (szerokość, długość, pełna nazwa) przez Nominatim (OSM)."""
    query = query.strip()
    if not query:
        return None

    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": 1})
    url = f"{NOMINATIM_URL}?{params}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None

    if not data:
        return None

    result = data[0]
    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    display_name = result.get("display_name", query)
    return latitude, longitude, display_name
