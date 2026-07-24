import pandas as pd

df = pd.read_csv("data/raw/training_log.csv", parse_dates=["date"])

df["pct_of_max"] = (df["weight_kg"] / df["pre_block_max_kg"] * 100).round(1)
df["volume_kg"] = df["reps"] * df["weight_kg"]

weekly_pattern = (df.groupby(["exercise", "week_num"])
                    .agg(
                        avg_pct_of_max=("pct_of_max", "mean"),
                        max_pct_of_max=("pct_of_max", "max"),
                        total_volume_kg=("volume_kg", "sum"),
                        avg_reps=("reps", "mean"),
                        num_sets=("reps", "count"),
                        session_types=("session_type", lambda s: "/".join(sorted(set(s))))
                    )
                    .reset_index()
                    .sort_values(["exercise", "week_num"]))

weekly_pattern.to_csv("data/processed/weekly_programming_patterns.csv", index=False)
print(weekly_pattern.to_string(index=False))

