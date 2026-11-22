from models import Hospital

# 6 mock hospitals using real Bangalore hospital names and approximate coordinates
HOSPITALS = [
    Hospital(
        id="HOSP-01",
        name="Manipal Hospital",
        lat=12.9592,
        lon=77.6473,
        icu_beds_available=6,
        specialties=["trauma", "cardiology", "neurology"],
    ),
    Hospital(
        id="HOSP-02",
        name="Fortis Hospital",
        lat=12.9618,
        lon=77.7108,
        icu_beds_available=4,
        specialties=["cardiology", "oncology", "orthopedics"],
    ),
    Hospital(
        id="HOSP-03",
        name="St. John's Medical College Hospital",
        lat=12.9345,
        lon=77.6191,
        icu_beds_available=8,
        specialties=["trauma", "general surgery", "pediatrics"],
    ),
    Hospital(
        id="HOSP-04",
        name="Apollo Hospital",
        lat=12.9282,
        lon=77.6753,
        icu_beds_available=5,
        specialties=["cardiology", "neurology", "trauma"],
    ),
    Hospital(
        id="HOSP-05",
        name="Narayana Health",
        lat=12.8405,
        lon=77.6477,
        icu_beds_available=7,
        specialties=["cardiology", "trauma", "general surgery"],
    ),
    Hospital(
        id="HOSP-06",
        name="Victoria Hospital",
        lat=12.9634,
        lon=77.5718,
        icu_beds_available=2,
        specialties=["general surgery", "orthopedics", "emergency"],
    ),
]
