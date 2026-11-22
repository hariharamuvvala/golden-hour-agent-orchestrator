from models import Ambulance

# 10 mock ambulances spread across Bangalore neighborhoods
# Center: 12.9716° N, 77.5946° E  —  spread ± 0.05°
AMBULANCES = [
    Ambulance(
        id="BLR-01",
        name="Ambulance BLR-01 (Koramangala)",
        lat=12.9279,
        lon=77.6271,
        status="available",
    ),
    Ambulance(
        id="BLR-02",
        name="Ambulance BLR-02 (Whitefield)",
        lat=12.9698,
        lon=77.7500,
        status="available",
    ),
    Ambulance(
        id="BLR-03",
        name="Ambulance BLR-03 (Jayanagar)",
        lat=12.9252,
        lon=77.5832,
        status="available",
    ),
    Ambulance(
        id="BLR-04",
        name="Ambulance BLR-04 (Hebbal)",
        lat=13.0350,
        lon=77.5970,
        status="available",
    ),
    Ambulance(
        id="BLR-05",
        name="Ambulance BLR-05 (Indiranagar)",
        lat=12.9784,
        lon=77.6408,
        status="available",
    ),
    Ambulance(
        id="BLR-06",
        name="Ambulance BLR-06 (Marathahalli)",
        lat=12.9591,
        lon=77.6974,
        status="available",
    ),
    Ambulance(
        id="BLR-07",
        name="Ambulance BLR-07 (HSR Layout)",
        lat=12.9116,
        lon=77.6474,
        status="available",
    ),
    Ambulance(
        id="BLR-08",
        name="Ambulance BLR-08 (Electronic City)",
        lat=12.8399,
        lon=77.6770,
        status="available",
    ),
    Ambulance(
        id="BLR-09",
        name="Ambulance BLR-09 (Rajajinagar)",
        lat=12.9906,
        lon=77.5520,
        status="available",
    ),
    Ambulance(
        id="BLR-10",
        name="Ambulance BLR-10 (Yelahanka)",
        lat=13.1007,
        lon=77.5963,
        status="available",
    ),
]
