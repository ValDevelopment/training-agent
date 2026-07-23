from importlib import import_module
import re
import streamlit as st


generator_module = import_module("04_program_generator")

generate_program = generator_module.generate_program


st.set_page_config(
    page_title="ValAI - High Intensity Strength Training Coach",
    page_icon="🏋️",
    layout="centered",
)
with st.sidebar:
    st.header("Settings")

    unit = st.radio(
        "Weight unit",
        options=["kg", "lb"],
        horizontal=True,
        key="weight_unit",
    )

    st.divider()

    if st.button(
        "Clear chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()
st.title("ValAI - High Intensity Strength Training Coach")

st.write(
    "Enter your squat, bench, and deadlift maxes, "
    "and I’ll generate an SBD program."
)


def display_program(grouped_program):
    lift_order = ["squat", "bench", "deadlift"]

    for exercise in lift_order:
        exercise_data = grouped_program[
            grouped_program["exercise"] == exercise
        ]

        if exercise_data.empty:
            continue

        with st.expander(exercise.title(), expanded=False):
            weeks = list(
                exercise_data.groupby("week_num", sort=True)
            )

            for start in range(0, len(weeks), 2):
                row_weeks = weeks[start:start + 2]
                columns = st.columns(len(row_weeks))

                for column, (week_num, week_data) in zip(
                    columns,
                    row_weeks,
                ):
                    with column:
                        st.markdown(f"### Week {week_num}")

                        if exercise == "squat" and week_num == 8:
                            st.markdown("**Session 1**")
                            st.markdown("- Test new max")

                            st.markdown("**Session 2**")
                            st.markdown("- Rest (optional)")

                            continue

                        for day_num, day_data in week_data.groupby(
                            "day_num",
                            sort=True,
                        ):
                            st.markdown(f"**Session {day_num}**")

                            for prescription in day_data["prescription"]:
                                st.markdown(f"- {prescription}")

                            st.markdown("")



if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and "program" in message
        ):
            display_program(message["program"])

user_message = st.chat_input(
    "Example: My squat is 180 kg, bench is 125 kg, "
    "and deadlift is 220 kg."
)

def extract_maxes(user_message):
    text = user_message.lower().strip()
    maxes = {}

    # Case 1: explicit lift names in either order
    for lift in ["squat", "bench", "deadlift"]:
        lift_then_number = rf"\b{lift}\b\D{{0,15}}(\d+(?:\.\d+)?)"
        number_then_lift = rf"(\d+(?:\.\d+)?)\D{{0,15}}\b{lift}\b"

        match = re.search(lift_then_number, text)

        if not match:
            match = re.search(number_then_lift, text)

        if match:
            maxes[lift] = float(match.group(1))

    # Case 2: shorthand such as "SBD 120 130 140"
    if len(maxes) < 3 and re.search(r"\bsbd\b", text):
        numbers = re.findall(r"\d+(?:\.\d+)?", text)

        if len(numbers) >= 3:
            maxes = {
                "squat": float(numbers[0]),
                "bench": float(numbers[1]),
                "deadlift": float(numbers[2]),
            }

    return maxes



if user_message:
    user_chat_message = {
        "role": "user",
        "content": user_message,
    }

    st.session_state.messages.append(user_chat_message)

    with st.chat_message("user"):
        st.markdown(user_message)

    current_maxes = extract_maxes(user_message)
    if unit == "lb":
        current_maxes = {
            lift: value * 0.453592
            for lift, value in current_maxes.items()
        }

    try:
        program, grouped_program = generate_program(current_maxes)
        if unit == "lb":
            grouped_program = grouped_program.copy()

            grouped_program["prescribed_weight_kg"] = (
                grouped_program["prescribed_weight_kg"] / 0.453592
            )

            grouped_program["prescription"] = (
                grouped_program["num_sets"].astype(str)
                + " x "
                + grouped_program["reps"].astype(str)
                + " @ "
                + grouped_program["prescribed_weight_kg"].round(1).astype(str)
                + " lb"
            )

        assistant_message = {
            "role": "assistant",
            "content": (
                "Your program is ready. "
                "Open a lift below to view its sessions."
            ),
            "program": grouped_program,
        }

    except Exception as error:
        assistant_message = {
            "role": "assistant",
            "content": f"Program generation failed: `{error}`",
        }

    st.session_state.messages.append(assistant_message)

    with st.chat_message("assistant"):
        st.markdown(assistant_message["content"])

        if "program" in assistant_message:
            display_program(assistant_message["program"])
