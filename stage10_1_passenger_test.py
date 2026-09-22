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


print("=" * 70)
print("STAGE 10.1 - PASSENGER ASSISTANCE DATA MODEL")
print("=" * 70)


# ------------------------------------------------------------
# Create a passenger journey
# ------------------------------------------------------------

passenger = PassengerRequest(
    train_number="12303",
    boarding_station="LLH",
    destination_station="BZL"
)


# ------------------------------------------------------------
# Display passenger information
# ------------------------------------------------------------

print("\nPassenger Journey")
print("-" * 40)

print(
    f"Train Number       : "
    f"{passenger.train_number}"
)

print(
    f"Boarding Station   : "
    f"{passenger.boarding_station}"
)

print(
    f"Destination Station: "
    f"{passenger.destination_station}"
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

assert passenger.train_number == "12303"

assert passenger.boarding_station == "LLH"

assert passenger.destination_station == "BZL"


print("\n✓ Passenger request created successfully.")
print("✓ Train number stored correctly.")
print("✓ Boarding station stored correctly.")
print("✓ Destination station stored correctly.")


print("\n" + "=" * 70)
print("STAGE 10.1: PASS")
print("=" * 70)