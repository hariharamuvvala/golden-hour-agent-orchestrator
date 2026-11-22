from typing import Optional

from agents.utils import haversine
from data.hospitals import HOSPITALS
from models import Hospital


class HospitalAgent:
    def find_nearest_hospital(self, lat: float, lon: float, severity: str) -> Optional[Hospital]:
        """Returns the best hospital with available ICU beds.

        For critical severity, trauma centres receive a 20% distance bonus
        (effective distance multiplied by 0.8) to prefer them over closer
        non-trauma hospitals.
        """
        candidates = [h for h in HOSPITALS if h.icu_beds_available > 0]
        if not candidates:
            return None

        def effective_distance(hospital: Hospital) -> float:
            dist = haversine(lat, lon, hospital.lat, hospital.lon)
            if severity == "critical" and "trauma" in hospital.specialties:
                dist *= 0.8
            return dist

        return min(candidates, key=effective_distance)
