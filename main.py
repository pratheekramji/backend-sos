from fastapi import FastAPI
from pydantic import BaseModel
import math

app = FastAPI()

# -----------------------------
# Data Models
# -----------------------------

class SOSRequest(BaseModel):
    patient_name: str
    phone: str
    latitude: float
    longitude: float
    online: bool


class LocationUpdate(BaseModel):
    ambulance_id: int
    latitude: float
    longitude: float


# -----------------------------
# Fake Database
# -----------------------------

ambulances = {
    1: {"driver_name": "Ravi", "phone": "9000000001"},
    2: {"driver_name": "Suresh", "phone": "9000000002"}
}

ambulance_locations = {
    1: {"latitude": 11.0200, "longitude": 76.9600},
    2: {"latitude": 11.0500, "longitude": 76.9500}
}

active_emergencies = {}


# -----------------------------
# Distance Function
# -----------------------------

def calculate_distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)


# -----------------------------
# Home API
# -----------------------------

@app.get("/")
def home():
    return {"message": "SOS Backend Running"}


# -----------------------------
# SOS API (ONLINE + OFFLINE)
# -----------------------------

@app.post("/sos")
def sos(request: SOSRequest):

    # OFFLINE MODE
    if request.online == False:

        sms_message = f"""
🚨 SOS EMERGENCY

Patient: {request.patient_name}
Phone: {request.phone}

Location:
https://maps.google.com/?q={request.latitude},{request.longitude}
"""

        return {
            "mode": "OFFLINE",
            "action": "Send this SMS to ambulance",
            "sms_message": sms_message
        }

    # ONLINE MODE

    nearest_ambulance = None
    min_distance = float("inf")

    for amb_id, loc in ambulance_locations.items():

        dist = calculate_distance(
            request.latitude,
            request.longitude,
            loc["latitude"],
            loc["longitude"]
        )

        if dist < min_distance:
            min_distance = dist
            nearest_ambulance = amb_id

    driver = ambulances[nearest_ambulance]

    active_emergencies[nearest_ambulance] = {
        "patient_name": request.patient_name,
        "phone": request.phone,
        "latitude": request.latitude,
        "longitude": request.longitude
    }

    return {
        "mode": "ONLINE",
        "ambulance_id": nearest_ambulance,
        "driver_name": driver["driver_name"],
        "driver_phone": driver["phone"]
    }


# -----------------------------
# Driver receives patient
# -----------------------------

@app.get("/driver-emergency/{ambulance_id}")
def driver_emergency(ambulance_id: int):

    if ambulance_id in active_emergencies:
        return active_emergencies[ambulance_id]

    return {"message": "No emergency assigned"}


# -----------------------------
# Driver GPS update
# -----------------------------

@app.post("/update-location")
def update_location(data: LocationUpdate):

    ambulance_locations[data.ambulance_id] = {
        "latitude": data.latitude,
        "longitude": data.longitude
    }

    return {"message": "Location updated"}


# -----------------------------
# Patient live tracking
# -----------------------------

@app.get("/track/{ambulance_id}")
def track(ambulance_id: int):

    if ambulance_id in ambulance_locations:
        return ambulance_locations[ambulance_id]

    return {"message": "Ambulance not found"}