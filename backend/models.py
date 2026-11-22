from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# Allowed enum values — rejected at parse time if violated
SeverityEnum = Literal["critical", "serious", "stable"]
StatusEnum   = Literal["available", "dispatched", "en_route"]


class Ambulance(BaseModel):
    id: str   = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    lat: float = Field(ge=-90.0,  le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    status: StatusEnum = "available"


class Hospital(BaseModel):
    id: str   = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    lat: float = Field(ge=-90.0,  le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    icu_beds_available: int = Field(ge=0, le=500)
    specialties: List[str] = Field(min_length=1)


class Emergency(BaseModel):
    id: str   = Field(min_length=1, max_length=36)
    patient_lat: float = Field(ge=-90.0,  le=90.0)
    patient_lon: float = Field(ge=-180.0, le=180.0)
    severity: SeverityEnum
    timestamp: str = Field(min_length=1, max_length=50)


class DispatchPlan(BaseModel):
    emergency_id: str = Field(min_length=1, max_length=36)
    ambulance: Ambulance
    hospital: Hospital
    distance_to_patient_km: float  = Field(ge=0.0)
    distance_to_hospital_km: float = Field(ge=0.0)
    estimated_eta_min: float       = Field(ge=0.0)
    reasoning: str = Field(min_length=1, max_length=500)
    severity: Optional[SeverityEnum] = None
