from typing import Optional

from agents.utils import haversine
from data.ambulances import AMBULANCES
from models import Ambulance


class DispatcherAgent:
    def find_nearest_ambulance(self, lat: float, lon: float) -> Optional[Ambulance]:
        """Returns the closest available ambulance to the given lat/lon, or None."""
        available = [a for a in AMBULANCES if a.status == "available"]
        if not available:
            return None
        return min(available, key=lambda a: haversine(lat, lon, a.lat, a.lon))
