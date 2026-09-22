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

import pandas as pd

# ============================================================
# FILE PATHS
# ============================================================

DATASET1_PATH = "ml_ready_segments.csv"
DATASET2_PATH = "ir_train.csv"


# ============================================================
# LOAD DATABASES
# ============================================================

print("Loading Database 1...")
db1 = pd.read_csv(DATASET1_PATH)

print("Loading Database 2...")
db2 = pd.read_csv(DATASET2_PATH)

print("✅ Both databases loaded successfully!")


# ============================================================
# GET TRAIN NUMBER
# ============================================================

train_number = input("\nEnter train number: ").strip()

print("\n" + "=" * 80)
print("TRAIN SEARCH")
print("=" * 80)

print("Searching for train:", train_number)


# ============================================================
# DATABASE 1
# ============================================================

print("\n" + "=" * 80)
print("DATABASE 1 - ROUTE INFORMATION")
print("=" * 80)

db1_train = db1[
    db1["train_number"].astype(str).str.strip() == train_number
].copy()

if len(db1_train) == 0:

    print("❌ Train not found in Database 1")

else:

    print("✅ Train found in Database 1")
    print("Number of route segments:", len(db1_train))

    print("\nRoute segments:")

    print(
        db1_train.to_string(index=False)
    )


# ============================================================
# DATABASE 2
# ============================================================

print("\n" + "=" * 80)
print("DATABASE 2 - HISTORICAL INFORMATION")
print("=" * 80)

db2_train = db2[
    db2["train_number"].astype(str).str.strip() == train_number
].copy()

if len(db2_train) == 0:

    print("❌ Train not found in Database 2")

else:

    print("✅ Train found in Database 2")
    print("Number of historical records:", len(db2_train))

    print("\nFirst 10 historical records:")

    print(
        db2_train.head(10).to_string(index=False)
    )


# ============================================================
# RELATIONSHIP
# ============================================================

print("\n" + "=" * 80)
print("DATABASE 1 ↔ DATABASE 2 RELATIONSHIP")
print("=" * 80)

if len(db1_train) > 0 and len(db2_train) > 0:

    print("✅ MATCH FOUND!")

    print("\nRelationship key:")
    print("train_number")

    print("\nDatabase 1:")
    print("Route segments =", len(db1_train))

    print("\nDatabase 2:")
    print("Historical records =", len(db2_train))

    print("\nTherefore:")

    print(
        f"Train {train_number} exists in BOTH databases."
    )

else:

    print("❌ Train does not exist in both databases.")


print("\n" + "=" * 80)
print("SEARCH COMPLETED")
print("=" * 80)