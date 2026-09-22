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
from passenger_assistance_engine import (
    create_assistance_response
)


print("=" * 70)
print("STAGE 10.6 - PASSENGER ASSISTANCE INTEGRATION")
print("=" * 70)


# ============================================================
# PASSENGER JOURNEY
# ============================================================

passenger = PassengerRequest(
    train_number="12303",
    boarding_station="LLH",
    destination_station="BZL"
)


# ============================================================
# DYNAMIC ETA ENGINE OUTPUT
# ============================================================

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


# ============================================================
# CURRENT TRAIN DELAY
# ============================================================

current_arrival_delay = 17


# ============================================================
# GENERATE FINAL RESPONSE
# ============================================================

response = create_assistance_response(
    passenger,
    eta_results,
    current_arrival_delay
)


# ============================================================
# DISPLAY
# ============================================================

print("\nPassenger Journey Status")
print("-" * 40)

print(
    f"Train              : "
    f"{response['train_number']}"
)

print(
    f"Boarding Station   : "
    f"{response['boarding_station']}"
)

print(
    f"Destination        : "
    f"{response['destination_station']}"
)

print(
    f"Current Delay      : "
    f"{response['current_delay_minutes']} minutes"
)

print(
    f"Delay Status       : "
    f"{response['delay_status']}"
)

print(
    f"Predicted ETA      : "
    f"{response['predicted_eta']}"
)

print(
    f"Remaining Time     : "
    f"{response['remaining_minutes']:.2f} minutes"
)

print(
    f"\nMessage:\n"
    f"{response['message']}"
)


# ============================================================
# VALIDATION
# ============================================================

assert response["status"] == "OK"

assert response["train_number"] == "12303"

assert response["boarding_station"] == "LLH"

assert response["destination_station"] == "BZL"

assert response["current_delay_minutes"] == 17

assert response["delay_status"] == "DELAYED"

assert response["predicted_eta"] == (
    "2024-09-26 08:27:55"
)

assert response["remaining_minutes"] == 10.93


print("\n✓ Passenger journey identified.")

print("✓ Destination detected.")

print("✓ Destination ETA retrieved.")

print("✓ Current train delay processed.")

print("✓ Delay status generated.")

print("✓ Final passenger response generated.")


# ============================================================
# UNKNOWN DESTINATION TEST
# ============================================================

unknown_passenger = PassengerRequest(
    train_number="12303",
    boarding_station="LLH",
    destination_station="ABC"
)


unknown_response = create_assistance_response(
    unknown_passenger,
    eta_results,
    current_arrival_delay
)


assert (
    unknown_response["status"]
    == "DESTINATION_NOT_FOUND"
)


print(
    "✓ Unknown destination handled correctly."
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("STAGE 10.6: PASS")
print("=" * 70)