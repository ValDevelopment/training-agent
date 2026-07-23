import pandas as pd

template = pd.read_csv("sbd_programming_template.csv")

current_maxes = {
    "squat": 155,
    "bench": 120,
    "deadlift": 160,
}

template["prescribed_weight_kg"] = template.apply(
    lambda row: current_maxes[row["exercise"]] * row["pct_of_max"] / 100,
    axis=1
)

template["prescribed_weight_kg"] = (
    template["prescribed_weight_kg"] / 1.25
).round() * 1.25

print(
    template[
        [
            "exercise",
            "week_num",
            "day_num",
            "set_id",
            "reps",
            "pct_of_max",
            "prescribed_weight_kg",
        ]
    ].head(10)
)
template = template.sort_values(
    ["week_num", "day_num", "exercise", "set_id"]
).reset_index(drop=True)
template.to_csv("generated_sbd_program.csv", index=False)

print("Saved to generated_sbd_program.csv")

grouped_program = (
    template
    .groupby(
        [
            "week_num",
            "day_num",
            "exercise",
            "reps",
            "prescribed_weight_kg",
            "session_type",
        ],
        as_index=False,
    )
    .agg(num_sets=("set_id", "count"))
)

grouped_program["prescription"] = (
    grouped_program["num_sets"].astype(str)
    + " x "
    + grouped_program["reps"].astype(str)
    + " @ "
    + grouped_program["prescribed_weight_kg"].astype(str)
    + " kg"
)

print(grouped_program.head(15))

grouped_program.to_csv("generated_sbd_program_readable.csv", index=False)

print("Saved to generated_sbd_program_readable.csv")

def generate_program(current_maxes):
    program = pd.read_csv("sbd_programming_template.csv")

    program["prescribed_weight_kg"] = program.apply(
        lambda row: (
            current_maxes[row["exercise"]]
            * row["pct_of_max"]
            / 100
        ),
        axis=1,
    )

    program["prescribed_weight_kg"] = (
        program["prescribed_weight_kg"] / 1.25
    ).round() * 1.25

    program = program.sort_values(
        ["exercise", "week_num", "day_num", "set_id"]
    ).reset_index(drop=True)

    # Identify when the set prescription changes.
    group_columns = [
        "exercise",
        "week_num",
        "day_num",
        "reps",
        "prescribed_weight_kg",
        "session_type",
    ]

    program["sequence_group"] = (
        program[group_columns]
        .ne(program[group_columns].shift())
        .any(axis=1)
        .cumsum()
    )

    grouped = (
        program
        .groupby("sequence_group", sort=False, as_index=False)
        .agg(
            exercise=("exercise", "first"),
            week_num=("week_num", "first"),
            day_num=("day_num", "first"),
            first_set_id=("set_id", "first"),
            reps=("reps", "first"),
            prescribed_weight_kg=("prescribed_weight_kg", "first"),
            session_type=("session_type", "first"),
            num_sets=("set_id", "count"),
        )
    )

    grouped["prescription"] = (
        grouped["num_sets"].astype(str)
        + " x "
        + grouped["reps"].astype(str)
        + " @ "
        + grouped["prescribed_weight_kg"].astype(str)
        + " kg"
    )

    grouped = grouped.sort_values(
        ["exercise", "week_num", "day_num", "first_set_id"]
    ).reset_index(drop=True)

    program = program.drop(columns=["sequence_group"])

    return program, grouped

program, grouped_program = generate_program(current_maxes)


def format_program(grouped_program):
    lines = []

    for exercise, exercise_data in grouped_program.groupby(
        "exercise",
        sort=False,
    ):
        lines.append(f"# {exercise.title()}")
        lines.append("")

        for week_num, week_data in exercise_data.groupby(
            "week_num",
            sort=True,
        ):
            lines.append(f"## Week {week_num}")
            lines.append("")

            for day_num, day_data in week_data.groupby(
                "day_num",
                sort=True,
            ):
                lines.append(f"### Session {day_num}")
                lines.append("")

                for prescription in day_data["prescription"]:
                    lines.append(f"- {prescription}")

                lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)

program, grouped_program = generate_program(current_maxes)

formatted_program = format_program(grouped_program)

print(formatted_program)

