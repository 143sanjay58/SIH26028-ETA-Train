# WINDOWS_CONSOLE_UTF8_FIX
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
try:
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from passenger_request import PassengerRequest
from passenger_assistance import create_passenger_assistance


print("=" * 70)
print("STAGE 10.4 - PASSENGER JOURNEY ASSISTANCE")
print("=" * 70)


# ------------------------------------------------------------
# Passenger journey
# ------------------------------------------------------------

passenger = PassengerRequest(
    train_number="12303",
    boarding_station="LLH",
    destination_station="BZL"
)


# ------------------------------------------------------------
# ETA Engine output
# ------------------------------------------------------------

eta_results = [

    {
        "station": "BLY",
        "eta": "2024-09-26 08:25:38",
        "remaining_minutes": 8.65
    },

    {
        "station": "BZL",
        "eta": "2024-09-26 08:27:55",
        "remaining_minutes": 10.93
    },

    {
        "station": "DKAE",
        "eta": "2024-09-26 08:30:55",
        "remaining_minutes": 13.93
    }
]


# ------------------------------------------------------------
# Generate passenger assistance
# ------------------------------------------------------------

response = create_passenger_assistance(
    passenger,
    eta_results
)


# ------------------------------------------------------------
# Display result
# ------------------------------------------------------------

print("\nPassenger Assistance Result")
print("-" * 40)

for key, value in response.items():

    print(
        f"{key}: {value}"
    )


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

assert response["status"] == "OK"

assert response["train_number"] == "12303"

assert response["boarding_station"] == "LLH"

assert response["destination_station"] == "BZL"

assert response["predicted_eta"] == "2024-09-26 08:27:55"

assert response["remaining_minutes"] == 10.93


print("\n✓ Passenger journey identified.")

print("✓ Destination ETA retrieved.")

print("✓ Remaining travel time retrieved.")

print("✓ Passenger-friendly response generated.")


# ------------------------------------------------------------
# Test unavailable destination
# ------------------------------------------------------------

unknown_passenger = PassengerRequest(
    train_number="12303",
    boarding_station="LLH",
    destination_station="ABC"
)


unknown_response = create_passenger_assistance(
    unknown_passenger,
    eta_results
)


assert (
    unknown_response["status"]
    == "DESTINATION_NOT_FOUND"
)


print(
    "✓ Unknown destination handled correctly."
)


print("\n" + "=" * 70)
print("STAGE 10.4: PASS")
print("=" * 70)
