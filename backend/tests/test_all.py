"""
Unit tests for Golden Hour Agent Orchestrator.

Covers:
  - Haversine utility
  - Pydantic model validation (valid + invalid inputs)
  - DispatcherAgent
  - HospitalAgent
  - CoordinatorAgent
  - FastAPI endpoints: /health, /status, POST /dispatch
"""

import sys
import os
import pytest

# Make backend/ importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_data():
    """Reset ambulance statuses and hospital ICU beds to initial values."""
    from data.ambulances import AMBULANCES
    from data.hospitals import HOSPITALS
    for a in AMBULANCES:
        a.status = "available"
    # restore original ICU bed counts (as defined in hospitals.py)
    original = [6, 4, 8, 5, 7, 2]
    for h, beds in zip(HOSPITALS, original):
        h.icu_beds_available = beds


# ---------------------------------------------------------------------------
# 1. Haversine utility
# ---------------------------------------------------------------------------

class TestHaversine:
    def test_same_point_is_zero(self):
        from agents.utils import haversine
        assert haversine(12.9716, 77.5946, 12.9716, 77.5946) == 0.0

    def test_known_distance(self):
        """Koramangala to Indiranagar ~4 km."""
        from agents.utils import haversine
        dist = haversine(12.9279, 77.6271, 12.9784, 77.6408)
        assert 3.0 < dist < 7.0

    def test_symmetry(self):
        from agents.utils import haversine
        a = haversine(12.92, 77.55, 13.02, 77.65)
        b = haversine(13.02, 77.65, 12.92, 77.55)
        assert abs(a - b) < 1e-9


# ---------------------------------------------------------------------------
# 2. Pydantic model validation
# ---------------------------------------------------------------------------

class TestModelValidation:
    def test_emergency_valid(self):
        from models import Emergency
        e = Emergency(id="abc123", patient_lat=12.97, patient_lon=77.59,
                      severity="critical", timestamp="2026-01-01T00:00:00Z")
        assert e.severity == "critical"

    def test_emergency_invalid_severity(self):
        from models import Emergency
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Emergency(id="x", patient_lat=12.97, patient_lon=77.59,
                      severity="unknown", timestamp="2026-01-01T00:00:00Z")

    def test_emergency_lat_out_of_range(self):
        from models import Emergency
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Emergency(id="x", patient_lat=99.0, patient_lon=77.59,
                      severity="stable", timestamp="2026-01-01T00:00:00Z")

    def test_ambulance_invalid_status(self):
        from models import Ambulance
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Ambulance(id="BLR-01", name="Test", lat=12.9, lon=77.5, status="broken")

    def test_hospital_negative_icu(self):
        from models import Hospital
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Hospital(id="H1", name="Test", lat=12.9, lon=77.5,
                     icu_beds_available=-1, specialties=["trauma"])


# ---------------------------------------------------------------------------
# 3. DispatcherAgent
# ---------------------------------------------------------------------------

class TestDispatcherAgent:
    def setup_method(self):
        _reset_data()

    def test_returns_nearest_available(self):
        from agents.dispatcher_agent import DispatcherAgent
        agent = DispatcherAgent()
        # Patient at city centre — BLR-09 (Rajajinagar) is closest
        result = agent.find_nearest_ambulance(12.9716, 77.5946)
        assert result is not None
        assert result.status == "available"

    def test_excludes_dispatched_ambulances(self):
        from agents.dispatcher_agent import DispatcherAgent
        from data.ambulances import AMBULANCES
        # Mark all but BLR-10 as dispatched
        for a in AMBULANCES:
            if a.id != "BLR-10":
                a.status = "dispatched"
        result = DispatcherAgent().find_nearest_ambulance(12.9716, 77.5946)
        assert result is not None
        assert result.id == "BLR-10"

    def test_returns_none_when_all_dispatched(self):
        from agents.dispatcher_agent import DispatcherAgent
        from data.ambulances import AMBULANCES
        for a in AMBULANCES:
            a.status = "dispatched"
        assert DispatcherAgent().find_nearest_ambulance(12.9716, 77.5946) is None


# ---------------------------------------------------------------------------
# 4. HospitalAgent
# ---------------------------------------------------------------------------

class TestHospitalAgent:
    def setup_method(self):
        _reset_data()

    def test_returns_hospital_with_icu(self):
        from agents.hospital_agent import HospitalAgent
        result = HospitalAgent().find_nearest_hospital(12.9716, 77.5946, "stable")
        assert result is not None
        assert result.icu_beds_available > 0

    def test_excludes_full_hospitals(self):
        from agents.hospital_agent import HospitalAgent
        from data.hospitals import HOSPITALS
        for h in HOSPITALS:
            h.icu_beds_available = 0
        assert HospitalAgent().find_nearest_hospital(12.9716, 77.5946, "critical") is None

    def test_critical_prefers_trauma_over_equidistant(self):
        """The 20% distance bonus for trauma hospitals should tip a close race.

        Patient is placed 30% of the way from Manipal (trauma) toward Victoria
        (no trauma): raw distance to Victoria is ~5.7 km, raw to Manipal ~2.5 km,
        effective Manipal = 2.5 × 0.8 = 2.0 km — Manipal wins.
        No other hospital has a lower effective distance from this point.
        """
        from agents.hospital_agent import HospitalAgent
        from data.hospitals import HOSPITALS

        manipal  = next(h for h in HOSPITALS if h.id == "HOSP-01")
        victoria = next(h for h in HOSPITALS if h.id == "HOSP-06")

        bias = 0.30
        lat = manipal.lat * (1 - bias) + victoria.lat * bias
        lon = manipal.lon * (1 - bias) + victoria.lon * bias

        result = HospitalAgent().find_nearest_hospital(lat, lon, "critical")
        assert result is not None
        assert result.id == "HOSP-01", (
            f"Expected Manipal Hospital (trauma) to win via bonus, got {result.name}"
        )


# ---------------------------------------------------------------------------
# 5. CoordinatorAgent
# ---------------------------------------------------------------------------

class TestCoordinatorAgent:
    def setup_method(self):
        _reset_data()

    def _make_emergency(self, severity="serious"):
        from models import Emergency
        return Emergency(
            id="TEST01",
            patient_lat=12.9716,
            patient_lon=77.5946,
            severity=severity,
            timestamp="2026-01-01T00:00:00Z",
        )

    def test_dispatch_returns_plan(self):
        from agents.coordinator_agent import CoordinatorAgent
        plan = CoordinatorAgent().dispatch(self._make_emergency())
        assert plan is not None
        assert plan.emergency_id == "TEST01"
        assert plan.ambulance is not None
        assert plan.hospital is not None

    def test_eta_is_positive(self):
        from agents.coordinator_agent import CoordinatorAgent
        plan = CoordinatorAgent().dispatch(self._make_emergency())
        assert plan.estimated_eta_min > 0

    def test_distances_are_non_negative(self):
        from agents.coordinator_agent import CoordinatorAgent
        plan = CoordinatorAgent().dispatch(self._make_emergency())
        assert plan.distance_to_patient_km >= 0
        assert plan.distance_to_hospital_km >= 0

    def test_reasoning_contains_all_agents(self):
        from agents.coordinator_agent import CoordinatorAgent
        plan = CoordinatorAgent().dispatch(self._make_emergency())
        assert "[Dispatcher]" in plan.reasoning
        assert "[Hospital]" in plan.reasoning
        assert "[Coordinator]" in plan.reasoning

    def test_severity_propagated(self):
        from agents.coordinator_agent import CoordinatorAgent
        plan = CoordinatorAgent().dispatch(self._make_emergency("critical"))
        assert plan.severity == "critical"

    def test_returns_none_when_no_resources(self):
        from agents.coordinator_agent import CoordinatorAgent
        from data.ambulances import AMBULANCES
        from data.hospitals import HOSPITALS
        for a in AMBULANCES:
            a.status = "dispatched"
        for h in HOSPITALS:
            h.icu_beds_available = 0
        assert CoordinatorAgent().dispatch(self._make_emergency()) is None


# ---------------------------------------------------------------------------
# 6. FastAPI endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    from main import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_between_tests():
    _reset_data()
    yield
    _reset_data()


class TestHealthEndpoint:
    def test_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_security_headers_present(self, client):
        r = client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert r.headers.get("cache-control") == "no-store"


class TestStatusEndpoint:
    def test_returns_ambulances_and_hospitals(self, client):
        r = client.get("/status")
        assert r.status_code == 200
        data = r.json()
        assert len(data["ambulances"]) == 10
        assert len(data["hospitals"]) == 6

    def test_ambulance_has_required_fields(self, client):
        r = client.get("/status")
        amb = r.json()["ambulances"][0]
        for field in ("id", "name", "lat", "lon", "status"):
            assert field in amb

    def test_hospital_has_required_fields(self, client):
        r = client.get("/status")
        hosp = r.json()["hospitals"][0]
        for field in ("id", "name", "lat", "lon", "icu_beds_available", "specialties"):
            assert field in hosp


class TestManualDispatchEndpoint:
    def test_valid_dispatch_returns_plan(self, client):
        r = client.post("/dispatch", json={
            "lat": 12.9279, "lon": 77.6271, "severity": "critical"
        })
        assert r.status_code == 200
        data = r.json()
        assert data["emergency_id"].startswith("MANUAL-")
        assert data["ambulance"]["id"].startswith("BLR-")
        assert data["estimated_eta_min"] > 0

    def test_invalid_severity_rejected(self, client):
        r = client.post("/dispatch", json={
            "lat": 12.97, "lon": 77.59, "severity": "unknown"
        })
        assert r.status_code == 422

    def test_lat_out_of_bounds_rejected(self, client):
        # lat > 90 is invalid WGS-84
        r = client.post("/dispatch", json={
            "lat": 91.0, "lon": 77.59, "severity": "stable"
        })
        assert r.status_code == 422

    def test_lon_out_of_bounds_rejected(self, client):
        # lon > 180 is invalid WGS-84
        r = client.post("/dispatch", json={
            "lat": 12.97, "lon": 181.0, "severity": "stable"
        })
        assert r.status_code == 422

    def test_missing_fields_rejected(self, client):
        r = client.post("/dispatch", json={"lat": 12.97})
        assert r.status_code == 422

    def test_all_dispatched_returns_503(self, client):
        from data.ambulances import AMBULANCES
        for a in AMBULANCES:
            a.status = "dispatched"
        r = client.post("/dispatch", json={
            "lat": 12.97, "lon": 77.59, "severity": "stable"
        })
        assert r.status_code == 503
