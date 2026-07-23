from importlib import import_module

import streamlit as st


generator_module = import_module("04_program_generator")

generate_program = generator_module.generate_program


st.set_page_config(
    page_title="AI Powerlifting Coach",
    page_icon="🏋️",
    layout="centered",
)

st.title("AI Powerlifting Coach")

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


if user_message:
    user_chat_message = {
        "role": "user",
        "content": user_message,
    }

    st.session_state.messages.append(user_chat_message)

    with st.chat_message("user"):
        st.markdown(user_message)

    # Temporary hardcoded maxes.
    # The LLM will extract these from the user's message later.
    current_maxes = {
        "squat": 180,
        "bench": 125,
        "deadlift": 220,
    }

    try:
        program, grouped_program = generate_program(current_maxes)

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