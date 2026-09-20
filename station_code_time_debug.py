import pandas as pd


DATASET1_PATH = "ml_ready_segments.csv"

print("=" * 80)
print("STEP 3E - TIME COLUMN DEBUG")
print("=" * 80)

df = pd.read_csv(DATASET1_PATH)

print("\nDataset loaded")
print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\n" + "=" * 80)
print("ALL COLUMNS")
print("=" * 80)

for i, col in enumerate(df.columns, start=1):
    print(f"{i:2}. {col}")


# ============================================================
# SHOW SAMPLE ROW
# ============================================================

print("\n" + "=" * 80)
print("SAMPLE ROW")
print("=" * 80)

print(df.head(3).to_string(index=False))


# ============================================================
# FIND POSSIBLE TIME / DAY COLUMNS
# ============================================================

print("\n" + "=" * 80)
print("TIME / DAY RELATED COLUMNS")
print("=" * 80)

possible_columns = []

for col in df.columns:

    col_lower = col.lower()

    if (
        "time" in col_lower
        or "arrival" in col_lower
        or "departure" in col_lower
        or "day" in col_lower
    ):

        possible_columns.append(col)


for col in possible_columns:

    print(f"\n--- {col} ---")

    print(
        df[col]
        .head(10)
        .to_string(index=False)
    )


# ============================================================
# INSPECT SBI -> SBT
# ============================================================

print("\n" + "=" * 80)
print("SBI -> SBT RAW RECORDS")
print("=" * 80)

df["previous_to_station"] = (
    df.groupby("train_number")["to_station"]
    .shift(1)
)

sbi_sbt = df[
    (df["previous_to_station"] == "SBI")
    &
    (df["from_station"] == "SBT")
].copy()

print("Records found:", len(sbi_sbt))

if len(sbi_sbt) > 0:

    print(
        sbi_sbt.head(20).to_string(index=False)
    )


# ============================================================
# INSPECT SBT -> SBI
# ============================================================

print("\n" + "=" * 80)
print("SBT -> SBI RAW RECORDS")
print("=" * 80)

sbt_sbi = df[
    (df["previous_to_station"] == "SBT")
    &
    (df["from_station"] == "SBI")
].copy()

print("Records found:", len(sbt_sbi))

if len(sbt_sbi) > 0:

    print(
        sbt_sbi.head(20).to_string(index=False)
    )


# ============================================================
# CHECK DATA TYPES
# ============================================================

print("\n" + "=" * 80)
print("DATA TYPES")
print("=" * 80)

print(
    df.dtypes.to_string()
)


print("\n" + "=" * 80)
print("DEBUG COMPLETED")
print("=" * 80)