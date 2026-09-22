import pandas as pd
import numpy as np

# ============================================================
# STEP 3J
# FINAL DATASET AUDIT
# ============================================================

INPUT_FILE = "ml_ready_segments_final.csv"

print("=" * 80)
print("STEP 3J - MISSING-VALUE & FINAL DATASET AUDIT")
print("=" * 80)


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("\nLoading final Dataset 1...")

df = pd.read_csv(INPUT_FILE)

print("Dataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# ============================================================
# 2. DISPLAY COLUMNS
# ============================================================

print("\n" + "=" * 80)
print("DATASET COLUMNS")
print("=" * 80)

for i, column in enumerate(df.columns, start=1):
    print(f"{i:2}. {column}")


# ============================================================
# 3. BASIC DATASET INFORMATION
# ============================================================

print("\n" + "=" * 80)
print("BASIC DATASET INFORMATION")
print("=" * 80)

print("Total rows:", len(df))
print("Total columns:", len(df.columns))
print("Unique trains:", df["train_number"].nunique())
print("Duplicate complete rows:", df.duplicated().sum())


# ============================================================
# 4. MISSING VALUES BY COLUMN
# ============================================================

print("\n" + "=" * 80)
print("MISSING VALUES BY COLUMN")
print("=" * 80)

missing_counts = df.isna().sum()

missing_percentages = (
    missing_counts / len(df) * 100
)

missing_table = pd.DataFrame({
    "column": df.columns,
    "missing_count": missing_counts.values,
    "missing_percentage": missing_percentages.values
})

missing_table = missing_table[
    missing_table["missing_count"] > 0
].sort_values(
    "missing_count",
    ascending=False
)


if len(missing_table) > 0:

    print(
        missing_table.to_string(index=False)
    )

else:

    print("\nNo missing values found.")


print(
    "\nTotal missing values:",
    int(missing_counts.sum())
)


# ============================================================
# 5. CHECK CRITICAL COLUMNS
# ============================================================

print("\n" + "=" * 80)
print("CRITICAL COLUMN CHECK")
print("=" * 80)

critical_columns = [
    "train_number",
    "from_station",
    "from_station_name",
    "from_station_canonical",
    "to_station",
    "to_station_name",
    "to_station_canonical",
    "scheduled_run_minutes",
]


for column in critical_columns:

    count = df[column].isna().sum()

    print(
        f"{column:<30} missing = {int(count)}"
    )


# ============================================================
# 6. TIME COLUMN MISSING VALUES
# ============================================================

print("\n" + "=" * 80)
print("TIME COLUMN AUDIT")
print("=" * 80)

time_columns = [
    "from_arrival",
    "from_departure",
    "to_arrival",
    "to_departure",
]


for column in time_columns:

    count = df[column].isna().sum()

    percentage = (
        count / len(df) * 100
    )

    print(
        f"{column:<20} "
        f"missing = {int(count):6d} "
        f"({percentage:.2f}%)"
    )


# ============================================================
# 7. IDENTIFY ROWS WITH MISSING VALUES
# ============================================================

print("\n" + "=" * 80)
print("ROWS CONTAINING MISSING VALUES")
print("=" * 80)

rows_with_missing = df[
    df.isna().any(axis=1)
].copy()


print(
    "Rows containing at least one missing value:",
    len(rows_with_missing)
)


if len(rows_with_missing) > 0:

    print("\nSample rows:")

    print(
        rows_with_missing
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 8. FIRST STATION ARRIVAL CHECK
# ============================================================
# The first station of a train commonly has no arrival time.
#
# We check whether missing from_arrival / arrival-related
# values are concentrated around route origins.

print("\n" + "=" * 80)
print("FIRST-STATION MISSING ARRIVAL CHECK")
print("=" * 80)


first_segments = df[
    df["route_order"] == 1
].copy()


print(
    "First route segments:",
    len(first_segments)
)


first_from_arrival_missing = (
    first_segments["from_arrival"]
    .isna()
    .sum()
)


print(
    "First segments with missing from_arrival:",
    int(first_from_arrival_missing)
)


# ============================================================
# 9. NON-FIRST-STATION MISSING ARRIVAL CHECK
# ============================================================

non_first_segments = df[
    df["route_order"] != 1
].copy()


non_first_from_arrival_missing = (
    non_first_segments["from_arrival"]
    .isna()
    .sum()
)


print(
    "Non-first segments with missing from_arrival:",
    int(non_first_from_arrival_missing)
)


# ============================================================
# 10. MISSING FROM DEPARTURE
# ============================================================

missing_from_departure = (
    df["from_departure"]
    .isna()
)


print("\n" + "=" * 80)
print("MISSING FROM-DEPARTURE CHECK")
print("=" * 80)

print(
    "Rows with missing from_departure:",
    int(missing_from_departure.sum())
)


if missing_from_departure.sum() > 0:

    print("\nSample affected rows:")

    print(
        df[
            missing_from_departure
        ][
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_arrival",
                "from_departure",
                "to_arrival",
                "scheduled_run_minutes",
                "status",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 11. MISSING TO-ARRIVAL
# ============================================================

missing_to_arrival = (
    df["to_arrival"]
    .isna()
)


print("\n" + "=" * 80)
print("MISSING TO-ARRIVAL CHECK")
print("=" * 80)

print(
    "Rows with missing to_arrival:",
    int(missing_to_arrival.sum())
)


if missing_to_arrival.sum() > 0:

    print("\nSample affected rows:")

    print(
        df[
            missing_to_arrival
        ][
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_departure",
                "to_arrival",
                "to_departure",
                "scheduled_run_minutes",
                "status",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 12. MISSING TO-DEPARTURE
# ============================================================

missing_to_departure = (
    df["to_departure"]
    .isna()
)


print("\n" + "=" * 80)
print("MISSING TO-DEPARTURE CHECK")
print("=" * 80)

print(
    "Rows with missing to_departure:",
    int(missing_to_departure.sum())
)


if missing_to_departure.sum() > 0:

    print("\nSample affected rows:")

    print(
        df[
            missing_to_departure
        ][
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "to_arrival",
                "to_departure",
                "scheduled_run_minutes",
                "status",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 13. MISSING STATION INFORMATION
# ============================================================

print("\n" + "=" * 80)
print("STATION INFORMATION AUDIT")
print("=" * 80)


station_columns = [
    "from_station",
    "from_station_name",
    "from_station_canonical",
    "to_station",
    "to_station_name",
    "to_station_canonical",
]


for column in station_columns:

    count = df[column].isna().sum()

    print(
        f"{column:<30} missing = {int(count)}"
    )


# ============================================================
# 14. SCHEDULED RUN TIME AUDIT
# ============================================================

print("\n" + "=" * 80)
print("SCHEDULED RUN TIME AUDIT")
print("=" * 80)


run_time_missing = (
    df["scheduled_run_minutes"]
    .isna()
    .sum()
)


negative_run_time = (
    df["scheduled_run_minutes"] < 0
).sum()


zero_run_time = (
    df["scheduled_run_minutes"] == 0
).sum()


print(
    "Missing scheduled_run_minutes:",
    int(run_time_missing)
)

print(
    "Negative scheduled_run_minutes:",
    int(negative_run_time)
)

print(
    "Zero scheduled_run_minutes:",
    int(zero_run_time)
)


print(
    "\nMinimum:",
    df["scheduled_run_minutes"].min()
)

print(
    "Maximum:",
    df["scheduled_run_minutes"].max()
)

print(
    "Mean:",
    round(
        df["scheduled_run_minutes"].mean(),
        2
    )
)

print(
    "Median:",
    df["scheduled_run_minutes"].median()
)


# ============================================================
# 15. LONG SEGMENT AUDIT
# ============================================================

print("\n" + "=" * 80)
print("LONG SEGMENT AUDIT")
print("=" * 80)


long_segments = df[
    df["scheduled_run_minutes"] >= 180
].copy()


print(
    "Segments >= 180 minutes:",
    len(long_segments)
)


if len(long_segments) > 0:

    print("\nLong segments:")

    print(
        long_segments[
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_station_name",
                "to_station_name",
                "from_day",
                "to_day",
                "scheduled_run_minutes",
                "status",
            ]
        ]
        .sort_values(
            "scheduled_run_minutes",
            ascending=False
        )
        .to_string(index=False)
    )


# ============================================================
# 16. OVERNIGHT SEGMENT AUDIT
# ============================================================

print("\n" + "=" * 80)
print("OVERNIGHT SEGMENT AUDIT")
print("=" * 80)


overnight_segments = df[
    df["is_overnight"] == True
].copy()


print(
    "Overnight segments:",
    len(overnight_segments)
)


if len(overnight_segments) > 0:

    print("\nSample overnight segments:")

    print(
        overnight_segments[
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_arrival",
                "from_departure",
                "to_arrival",
                "to_departure",
                "from_day",
                "to_day",
                "scheduled_run_minutes",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 17. SAME CANONICAL STATION AUDIT
# ============================================================

print("\n" + "=" * 80)
print("SAME CANONICAL STATION AUDIT")
print("=" * 80)


same_canonical = df[
    df["same_canonical_station"] == True
].copy()


print(
    "Same canonical station segments:",
    len(same_canonical)
)


if len(same_canonical) > 0:

    print("\nSample same-canonical segments:")

    print(
        same_canonical[
            [
                "train_number",
                "route_order",
                "from_station",
                "to_station",
                "from_station_canonical",
                "to_station_canonical",
                "scheduled_run_minutes",
            ]
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# 18. ROUTE ORDER AUDIT
# ============================================================

print("\n" + "=" * 80)
print("ROUTE ORDER AUDIT")
print("=" * 80)


route_order_missing = (
    df["route_order"]
    .isna()
    .sum()
)


route_order_min = (
    df.groupby("train_number")["route_order"]
      .min()
)


invalid_route_order_start = (
    route_order_min != 1
).sum()


print(
    "Missing route_order:",
    int(route_order_missing)
)

print(
    "Trains not starting at route_order = 1:",
    int(invalid_route_order_start)
)


# ============================================================
# 19. CANONICAL CODE AUDIT
# ============================================================

print("\n" + "=" * 80)
print("CANONICAL CODE AUDIT")
print("=" * 80)


canonical_from_missing = (
    df["from_station_canonical"]
    .isna()
    .sum()
)


canonical_to_missing = (
    df["to_station_canonical"]
    .isna()
    .sum()
)


print(
    "Missing canonical FROM codes:",
    int(canonical_from_missing)
)

print(
    "Missing canonical TO codes:",
    int(canonical_to_missing)
)


# ============================================================
# 20. CHECK NORMALIZED CONTINUITY
# ============================================================

print("\n" + "=" * 80)
print("FINAL CANONICAL ROUTE CONTINUITY")
print("=" * 80)


# Sort explicitly by train and route order
df_sorted = df.sort_values(
    [
        "train_number",
        "route_order"
    ]
).copy()


df_sorted["previous_to_canonical"] = (
    df_sorted
    .groupby("train_number")[
        "to_station_canonical"
    ]
    .shift(1)
)


valid_links = (
    df_sorted["previous_to_canonical"]
    .notna()
)


continuous_links = (
    (
        df_sorted.loc[
            valid_links,
            "previous_to_canonical"
        ]
        ==
        df_sorted.loc[
            valid_links,
            "from_station_canonical"
        ]
    )
    .sum()
)


total_links = valid_links.sum()


disconnected_links = (
    total_links -
    continuous_links
)


continuity_percentage = (
    continuous_links /
    total_links *
    100
)


print(
    "Total links:",
    int(total_links)
)

print(
    "Continuous links:",
    int(continuous_links)
)

print(
    "Disconnected links:",
    int(disconnected_links)
)

print(
    "Canonical continuity:",
    round(
        continuity_percentage,
        2
    ),
    "%"
)


# ============================================================
# 21. FINAL SANITY CHECKS
# ============================================================

print("\n" + "=" * 80)
print("FINAL SANITY CHECKS")
print("=" * 80)


checks = {}


checks["row_count_ok"] = (
    len(df) == 372911
)


checks["train_count_ok"] = (
    df["train_number"].nunique() == 5178
)


checks["duplicate_rows_ok"] = (
    df.duplicated().sum() == 0
)


checks["negative_run_time_ok"] = (
    negative_run_time == 0
)


checks["zero_run_time_ok"] = (
    zero_run_time == 0
)


checks["critical_station_missing_ok"] = (
    df[
        [
            "train_number",
            "from_station",
            "to_station",
            "from_station_canonical",
            "to_station_canonical",
            "scheduled_run_minutes",
        ]
    ]
    .isna()
    .sum()
    .sum()
    == 0
)


for check_name, result in checks.items():

    status = "PASS" if result else "FAIL"

    print(
        f"{check_name:<35} {status}"
    )


# ============================================================
# 22. SAVE AUDIT REPORT
# ============================================================

audit_report = pd.DataFrame(
    [
        {
            "metric":
                "total_rows",
            "value":
                len(df)
        },

        {
            "metric":
                "unique_trains",
            "value":
                df["train_number"].nunique()
        },

        {
            "metric":
                "duplicate_rows",
            "value":
                df.duplicated().sum()
        },

        {
            "metric":
                "total_missing_values",
            "value":
                int(missing_counts.sum())
        },

        {
            "metric":
                "overnight_segments",
            "value":
                len(overnight_segments)
        },

        {
            "metric":
                "long_segments",
            "value":
                len(long_segments)
        },

        {
            "metric":
                "same_canonical_segments",
            "value":
                len(same_canonical)
        },

        {
            "metric":
                "total_route_links",
            "value":
                int(total_links)
        },

        {
            "metric":
                "continuous_links",
            "value":
                int(continuous_links)
        },

        {
            "metric":
                "disconnected_links",
            "value":
                int(disconnected_links)
        },

        {
            "metric":
                "canonical_continuity_percentage",
            "value":
                round(
                    continuity_percentage,
                    4
                )
        },
    ]
)


AUDIT_OUTPUT = (
    "station_code_final_audit.csv"
)


audit_report.to_csv(
    AUDIT_OUTPUT,
    index=False
)


# ============================================================
# 23. FINAL RESULT
# ============================================================

print("\n" + "=" * 80)
print("STEP 3J FINAL RESULT")
print("=" * 80)


all_passed = all(
    checks.values()
)


if all_passed:

    print(
        "\nALL CORE SANITY CHECKS PASSED."
    )

    print(
        "\nDataset 1 is ready to be frozen."
    )

else:

    print(
        "\nWARNING: SOME SANITY CHECKS FAILED."
    )

    print(
        "\nDo NOT freeze Dataset 1 yet."
    )


print(
    "\nAudit report saved as:",
    AUDIT_OUTPUT
)


print(
    "\nOriginal ml_ready_segments.csv was NOT modified."
)


print("\n" + "=" * 80)
print("STEP 3J COMPLETED")
print("=" * 80)