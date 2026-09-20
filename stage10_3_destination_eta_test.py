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

from passenger_eta import get_destination_eta


print("=" * 70)
print("STAGE 10.3 - DESTINATION ETA RETRIEVAL")
print("=" * 70)


# ------------------------------------------------------------
# Simulated ETA Engine output
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
# Passenger destination
# ------------------------------------------------------------

destination = "BZL"


print("\nPassenger destination:")
print(destination)


print("\nSearching ETA predictions...")


# ------------------------------------------------------------
# Retrieve destination ETA
# ------------------------------------------------------------

result = get_destination_eta(
    eta_results,
    destination
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

assert result is not None

assert result["station"] == "BZL"


print("\n✓ Destination found in ETA predictions.")

print(
    f"Destination station : "
    f"{result['station']}"
)

print(
    f"Predicted ETA        : "
    f"{result['eta']}"
)

print(
    f"Remaining time       : "
    f"{result['remaining_minutes']:.2f} minutes"
)


# ------------------------------------------------------------
# Test destination not present
# ------------------------------------------------------------

missing_result = get_destination_eta(
    eta_results,
    "ABC"
)


assert missing_result is None


print("\n✓ Unknown destination handled correctly.")


print("\n" + "=" * 70)
print("STAGE 10.3: PASS")
print("=" * 70)