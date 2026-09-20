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

from passenger_destination import find_destination


print("=" * 70)
print("STAGE 10.2 - DESTINATION STATION DETECTION")
print("=" * 70)


# ------------------------------------------------------------
# Simulated upcoming stations
# ------------------------------------------------------------

upcoming_stations = [
    "BLY",
    "BZL",
    "DKAE",
    "GBRA",
    "JOX"
]


destination = "BZL"


print("\nPassenger destination:")
print(destination)


print("\nUpcoming stations:")
print(upcoming_stations)


# ------------------------------------------------------------
# Detect destination
# ------------------------------------------------------------

found = find_destination(
    upcoming_stations,
    destination
)


print("\nDestination detection result:")


if found:
    print(
        f"✓ Destination {destination} "
        f"is an upcoming station."
    )
else:
    print(
        f"✗ Destination {destination} "
        f"is not upcoming."
    )


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

assert found is True


# Test a station that isn't upcoming

not_found = find_destination(
    upcoming_stations,
    "ABC"
)

assert not_found is False


print("\n✓ Existing destination detected.")
print("✓ Non-existing destination rejected.")


print("\n" + "=" * 70)
print("STAGE 10.2: PASS")
print("=" * 70)