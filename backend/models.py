from typing import List, Optional
from pydantic import BaseModel


class Ambulance(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    status: str = "available"  # available | dispatched | en_route


class Hospital(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    icu_beds_available: int
    specialties: List[str]


class Emergency(BaseModel):
    id: str
    patient_lat: float
    patient_lon: float
    severity: str  # critical | serious | stable
    timestamp: str


class DispatchPlan(BaseModel):
    emergency_id: str
    ambulance: Ambulance
    hospital: Hospital
    distance_to_patient_km: float
    distance_to_hospital_km: float
    estimated_eta_min: float
    reasoning: str
    severity: Optional[str] = None
