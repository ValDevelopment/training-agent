import pandas as pd

weekly_pattern = pd.read_csv("data/processed/weekly_programming_patterns.csv")

training_log = pd.read_csv("data/raw/training_log.csv", parse_dates=["date"])


patterns_by_lift = {
    exercise: weekly_pattern[
        weekly_pattern["exercise"] == exercise
    ].reset_index(drop=True)
    for exercise in ["squat", "bench", "deadlift"]
}

squat_sets = (
    training_log[
        training_log["exercise"] == "squat"
    ]
    .sort_values(["week_num", "day_num", "set_id"])
    .reset_index(drop=True)
)

squat_sets["pct_of_max"] = (
    squat_sets["weight_kg"]
    / squat_sets["pre_block_max_kg"]
    * 100
).round(1)

squat_template = squat_sets[
    [
        "week_num",
        "day_num",
        "set_id",
        "reps",
        "pct_of_max",
        "session_type",
    ]
].copy()

squat_template.to_csv("data/templates/squat_programming_template.csv", index=False)


bench_sets = (
    training_log[
        training_log["exercise"] == "bench"
    ]
    .sort_values(["week_num", "day_num", "set_id"])
    .reset_index(drop=True)
)

bench_sets["pct_of_max"] = (
    bench_sets["weight_kg"]
    / bench_sets["pre_block_max_kg"]
    * 100
).round(1)

bench_template = bench_sets[
    [
        "week_num",
        "day_num",
        "set_id",
        "reps",
        "pct_of_max",
        "session_type",
    ]
].copy()

bench_template.to_csv("data/templates/bench_programming_template.csv", index=False)


deadlift_sets = (
    training_log[
        training_log["exercise"] == "deadlift"
    ]
    .sort_values(["week_num", "day_num", "set_id"])
    .reset_index(drop=True)
)

deadlift_sets["pct_of_max"] = (
    deadlift_sets["weight_kg"]
    / deadlift_sets["pre_block_max_kg"]
    * 100
).round(1)

deadlift_template = deadlift_sets[
    [
        "week_num",
        "day_num",
        "set_id",
        "reps",
        "pct_of_max",
        "session_type",
    ]
].copy()

deadlift_template.to_csv("data/templates/deadlift_programming_template.csv", index=False)


squat_template["exercise"] = "squat"
bench_template["exercise"] = "bench"
deadlift_template["exercise"] = "deadlift"

sbd_template = pd.concat(
    [squat_template, bench_template, deadlift_template],
    ignore_index=True
)

sbd_template = sbd_template[
    [
        "exercise",
        "week_num",
        "day_num",
        "set_id",
        "reps",
        "pct_of_max",
        "session_type",
    ]
]

sbd_template.to_csv("data/templates/sbd_programming_template.csv", index=False)

print(sbd_template.head())
print(sbd_template.shape)