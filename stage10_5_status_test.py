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

from passenger_status import get_delay_status


print("=" * 70)
print("STAGE 10.5 - DYNAMIC DELAY STATUS")
print("=" * 70)


# ------------------------------------------------------------
# Test different delay conditions
# ------------------------------------------------------------

test_cases = [
    (0, "ON TIME"),
    (10, "SLIGHTLY DELAYED"),
    (30, "DELAYED"),
    (90, "HEAVILY DELAYED")
]


print("\nDelay Status Tests")
print("-" * 40)


for delay, expected_status in test_cases:

    status = get_delay_status(delay)

    print(
        f"Delay: {delay:>3} min"
        f"  →  {status}"
    )

    assert status == expected_status


print("\n✓ On-time status detected.")

print("✓ Slight delay status detected.")

print("✓ Delayed status detected.")

print("✓ Heavy delay status detected.")


# ------------------------------------------------------------
# Test your SIH example
# ------------------------------------------------------------

current_delay = 17

status = get_delay_status(
    current_delay
)


print("\nSIH Passenger Example")
print("-" * 40)

print(
    f"Train 12303 delay: "
    f"{current_delay} minutes"
)

print(
    f"Passenger status: "
    f"{status}"
)


assert status == "DELAYED"


print("\n✓ Dynamic train delay converted "
      "into passenger status.")


print("\n" + "=" * 70)
print("STAGE 10.5: PASS")
print("=" * 70)