from typing import Optional

from agents.dispatcher_agent import DispatcherAgent
from agents.hospital_agent import HospitalAgent
from agents.utils import haversine
from models import DispatchPlan, Emergency


class CoordinatorAgent:
    def dispatch(self, emergency: Emergency) -> Optional[DispatchPlan]:
        """Calls both sub-agents and assembles a DispatchPlan, or returns None."""
        dispatcher = DispatcherAgent()
        hospital_agent = HospitalAgent()

        ambulance = dispatcher.find_nearest_ambulance(
            emergency.patient_lat, emergency.patient_lon
        )
        hospital = hospital_agent.find_nearest_hospital(
            emergency.patient_lat, emergency.patient_lon, emergency.severity
        )

        if ambulance is None or hospital is None:
            return None

        distance_to_patient_km = round(
            haversine(ambulance.lat, ambulance.lon, emergency.patient_lat, emergency.patient_lon),
            2,
        )
        distance_to_hospital_km = round(
            haversine(emergency.patient_lat, emergency.patient_lon, hospital.lat, hospital.lon),
            2,
        )
        estimated_eta_min = round(
            (distance_to_patient_km + distance_to_hospital_km) / 60 * 60, 1
        )

        reasoning = (
            f"[Dispatcher] {ambulance.id} is {distance_to_patient_km}km away near "
            f"{ambulance.name.split('(')[-1].rstrip(')')}. "
            f"[Hospital] {hospital.name} has {hospital.icu_beds_available} ICU beds "
            f"and is {distance_to_hospital_km}km away. "
            f"[Coordinator] Dispatching now. ETA: {estimated_eta_min} min."
        )

        return DispatchPlan(
            emergency_id=emergency.id,
            ambulance=ambulance,
            hospital=hospital,
            distance_to_patient_km=distance_to_patient_km,
            distance_to_hospital_km=distance_to_hospital_km,
            estimated_eta_min=estimated_eta_min,
            reasoning=reasoning,
            severity=emergency.severity,
        )
