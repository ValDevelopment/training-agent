from importlib import import_module
import re
import streamlit as st
import json
from groq import Groq
from src.program_generator import (
    generate_program,
    get_session,
    get_week,
    get_lift_summary,
    get_heaviest_set,
)

st.set_page_config(
    page_title="High Intensity Strength Programming Coach",
    page_icon="🏋️",
    layout="centered",
)
if "messages" not in st.session_state:
    st.session_state.messages = []
default_session_state = {
    "messages": [],
    "pending_maxes": None,
    "pending_displayed_maxes": None,
    "pending_unit": None,
    "active_displayed_maxes": None,
    "active_unit": None,
    "generated_program": None,
    "last_request_type": None,
}

groq_client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

for key, default_value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

with st.sidebar:
    st.header("Settings")

    unit = st.radio(
        "Weight unit",
        options=["kg", "lb"],
        horizontal=True,
        key="weight_unit",
    )

    if st.session_state.get("pending_displayed_maxes") is not None:
        maxes = st.session_state.pending_displayed_maxes
        shown_unit = st.session_state.pending_unit
        heading = "Pending maxes"

    elif st.session_state.get("active_displayed_maxes") is not None:
        maxes = st.session_state.active_displayed_maxes
        shown_unit = st.session_state.active_unit
        heading = "Program maxes"

    else:
        maxes = None
        shown_unit = None
        heading = None

    if maxes is not None:
        st.divider()
        st.subheader(heading)

        st.metric(
            "Squat",
            f"{maxes['squat']:.1f} {shown_unit}",
        )
        st.metric(
            "Bench",
            f"{maxes['bench']:.1f} {shown_unit}",
        )
        st.metric(
            "Deadlift",
            f"{maxes['deadlift']:.1f} {shown_unit}",
        )

    st.divider()

    if st.button(
        "Clear chat",
        use_container_width=True,
        key="clear_chat_button",
    ):

        
        st.session_state.messages = []

        st.session_state.pending_maxes = None
        st.session_state.pending_displayed_maxes = None
        st.session_state.pending_unit = None

        st.session_state.active_displayed_maxes = None
        st.session_state.active_unit = None

        st.session_state.generated_program = None

        st.session_state.last_request_type = None

        st.rerun()

st.title("High Intensity Strength Programming Coach")

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

st.caption(
    f"Using {unit}. Examples: "
    f"`squat 180 bench 125 deadlift 220` or `SBD 180 125 220`."
)

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

def extract_maxes_with_groq(user_message):
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract the user's squat, bench press, and "
                    "deadlift one-rep maxes. Return JSON only with "
                    "exactly these keys: squat, bench, deadlift. "
                    "Each value must be a number or null. "
                    "For shorthand such as 'SBD 180 120 220', "
                    "interpret the values as squat, bench, deadlift "
                    "in that order. Do not convert units."
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    content = response.choices[0].message.content
    extracted = json.loads(content)

    return {
        lift: float(extracted[lift])
        for lift in ["squat", "bench", "deadlift"]
        if extracted.get(lift) is not None
    }

def extract_session_request(user_message):
    text = user_message.lower().strip()

    exercise = None

    for lift in ["squat", "bench", "deadlift"]:
        if lift in text:
            exercise = lift
            break

    week_match = re.search(
        r"\bweek\s*(\d+)\b",
        text,
    )

    session_match = re.search(
        r"\b(?:session|day)\s*(\d+)\b",
        text,
    )

    if not exercise or not week_match:
        return None

    request = {
        "exercise": exercise,
        "week_num": int(week_match.group(1)),
        "day_num": None,
    }

    if session_match:
        request["day_num"] = int(session_match.group(1))

    st.session_state.last_request_type = "session"
    return request


def extract_lift_summary_request(user_message):
    text = user_message.lower().strip()

    if re.search(r"\b(?:week|session|day)\s*\d+\b", text):
        return None

    summary_phrases = [
        "summarize",
        "summary",
        "overview",
        "describe",
        "explain",
    ]

    has_summary_phrase = any(
        phrase in text
        for phrase in summary_phrases
    )

    is_context_followup = (
        st.session_state.get("last_request_type") == "summary"
        and any(
            phrase in text
            for phrase in ["what about", "how about"]
        )
    )

    if not has_summary_phrase and not is_context_followup:
        return None

    for lift in ["squat", "bench", "deadlift"]:
        st.session_state.last_request_type = "summary"
        if lift in text:
            return {
                "exercise": lift,
            }

    return None


def extract_heaviest_set_request(user_message):
    text = user_message.lower().strip()

    heaviest_phrases = [
        "heaviest",
        "highest weight",
        "max weight",
        "top weight",
    ]

    has_heaviest_phrase = any(
        phrase in text
        for phrase in heaviest_phrases
    )

    is_context_followup = (
        st.session_state.get("last_request_type") == "heaviest"
        and any(
            phrase in text
            for phrase in ["what about", "how about"]
        )
    )

    if not has_heaviest_phrase and not is_context_followup:
        return None

    for lift in ["squat", "bench", "deadlift"]:
        if lift in text:
            st.session_state.last_request_type = "heaviest"
            return {
                "exercise": lift,
            }

    return None


def explain_program(grouped_program, displayed_maxes, unit):
    program_summary = grouped_program[
        [
            "exercise",
            "week_num",
            "day_num",
            "prescription",
        ]
    ].to_dict(orient="records")

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the conversational assistant for a powerlifting "
                    "program generator. The program has already been generated "
                    "by a deterministic backend.\n\n"

                    "Explain the program confidently and directly. Do not use "
                    "phrases such as 'it appears', 'it seems', or 'may be'.\n\n"

                    "Only describe information that is explicitly present in the "
                    "provided program data. Do not infer deload weeks, recovery "
                    "weeks, training blocks, peaking phases, progressive overload, "
                    "or the purpose of unusual prescriptions unless that information "
                    "is explicitly supplied.\n\n"

                    "Do not mention or interpret individual week numbers. Do not "
                    "comment on unusual, low, or high weights. Do not criticize the "
                    "program and do not suggest changes.\n\n"

                    "Briefly tell the user that the program includes squat, bench, "
                    "and deadlift sessions, that the weights were calculated from "
                    "their supplied maxes, and that they can open each lift to view "
                    "the full schedule.\n\n"

                    "Keep the response between 50 and 90 words."
                ),
            },
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content



if user_message:
    user_chat_message = {
        "role": "user",
        "content": user_message,
    }

    st.session_state.messages.append(user_chat_message)

    try:
        session_request = extract_session_request(user_message)
        summary_request = extract_lift_summary_request(user_message)
        heaviest_request = extract_heaviest_set_request(user_message)



        if heaviest_request is not None:
            if st.session_state.generated_program is None:
                assistant_message = {
                    "role": "assistant",
                    "content": (
                        "Generate a program first, then I can find "
                        "the heaviest set for a lift."
                    ),
                }

            else:
                heaviest_data = get_heaviest_set(
                    st.session_state.generated_program,
                    heaviest_request["exercise"],
                )

                if heaviest_data is None:
                    assistant_message = {
                        "role": "assistant",
                        "content": (
                            "I could not find that lift in your "
                            "generated program."
                        ),
                    }

                else:
                    summary_unit = (
                        st.session_state.active_unit
                        or st.session_state.pending_unit
                        or unit
                    )

                    rows = []

                    for _, row in heaviest_data.iterrows():
                        weight_kg = row["prescribed_weight_kg"]

                        if summary_unit == "lb":
                            weight = weight_kg / 0.453592
                        else:
                            weight = weight_kg

                        rows.append(
                            f"- Week {int(row['week_num'])}, "
                            f"Session {int(row['day_num'])}: "
                            f"{weight:.1f} {summary_unit}"
                        )

                    formatted_rows = "\n".join(rows)

                    exercise = heaviest_request["exercise"]

                    assistant_message = {
                        "role": "assistant",
                        "content": (
                            f"**Heaviest {exercise} set**\n\n"
                            f"{formatted_rows}"
                        ),
                    }
        elif summary_request is not None:
            if st.session_state.generated_program is None:
                assistant_message = {
                    "role": "assistant",
                    "content": (
                        "Generate a program first, then I can summarize "
                        "a specific lift."
                    ),
                }

            else:
                lift_data = get_lift_summary(
                    st.session_state.generated_program,
                    summary_request["exercise"],
                )

                exercise = summary_request["exercise"]

                summary_data = lift_data.copy()

                extra_note = ""

                if exercise == "squat":
                    summary_data = summary_data[
                        summary_data["week_num"] != 8
                    ]

                    extra_note = (
                        "\n- Week 8 is a separate max-testing week "
                        "and is excluded from these training totals"
                    )

                if exercise == "squat":
                    summary_data = summary_data[
                        summary_data["week_num"] != 8
                    ]

                if lift_data is None:
                    assistant_message = {
                        "role": "assistant",
                        "content": (
                            "I could not find that lift in your "
                            "generated program."
                        ),
                    }

                else:
                    num_weeks = int(summary_data["week_num"].nunique())

                    num_sessions = int(
                        summary_data[
                            ["week_num", "day_num"]
                        ].drop_duplicates().shape[0]
                    )

                    total_sets = int(summary_data["num_sets"].sum())

                    min_weight_kg = summary_data[
                        "prescribed_weight_kg"
                    ].min()

                    max_weight_kg = summary_data[
                        "prescribed_weight_kg"
                    ].max()

                    summary_unit = (
                        st.session_state.active_unit
                        or st.session_state.pending_unit
                        or unit
                    )

                    if summary_unit == "lb":
                        min_weight = min_weight_kg / 0.453592
                        max_weight = max_weight_kg / 0.453592
                    else:
                        min_weight = min_weight_kg
                        max_weight = max_weight_kg

                    exercise = summary_request["exercise"]

                    assistant_message = {
                        "role": "assistant",
                        "content": (
                            f"**{exercise.title()} program summary**\n\n"
                            f"- {num_weeks} weeks\n"
                            f"- {num_sessions} sessions\n"
                            f"- {total_sets} total working sets\n"
                            f"- Prescribed weights range from "
                            f"{min_weight:.1f} {summary_unit} to "
                            f"{max_weight:.1f} {summary_unit}"
                            f"{extra_note}"
                        ),
                    }
        elif session_request is not None:
            if st.session_state.generated_program is None:
                assistant_message = {
                    "role": "assistant",
                    "content": (
                        "Generate a program first, then you can ask "
                        "about a specific lift, week, and session."
                    ),
                }

            else:
                # Specific session request
                if session_request["day_num"] is not None:
                    session_data = get_session(
                        st.session_state.generated_program,
                        session_request["exercise"],
                        session_request["week_num"],
                        session_request["day_num"],
                    )

                    if session_data is None:
                        assistant_message = {
                            "role": "assistant",
                            "content": (
                                "I could not find that session in your "
                                "generated program."
                            ),
                        }

                    else:
                        prescriptions = session_data[
                            "prescription"
                        ].tolist()

                        formatted_prescriptions = "\n".join(
                            f"- {prescription}"
                            for prescription in prescriptions
                        )

                        assistant_message = {
                            "role": "assistant",
                            "content": (
                                f"**{session_request['exercise'].title()} — "
                                f"Week {session_request['week_num']}, "
                                f"Session {session_request['day_num']}**\n\n"
                                f"{formatted_prescriptions}"
                            ),
                        }

                # Whole-week request
                else:
                    week_data = get_week(
                        st.session_state.generated_program,
                        session_request["exercise"],
                        session_request["week_num"],
                    )

                    if week_data is None:
                        assistant_message = {
                            "role": "assistant",
                            "content": (
                                "I could not find that week in your "
                                "generated program."
                            ),
                        }

                    else:
                        week_sections = []

                        for day_num, day_data in week_data.groupby(
                            "day_num",
                            sort=True,
                        ):
                            prescriptions = day_data[
                                "prescription"
                            ].tolist()

                            formatted_prescriptions = "\n".join(
                                f"- {prescription}"
                                for prescription in prescriptions
                            )

                            week_sections.append(
                                f"**Session {day_num}**\n"
                                f"{formatted_prescriptions}"
                            )

                        formatted_week = "\n\n".join(week_sections)

                        assistant_message = {
                            "role": "assistant",
                            "content": (
                                f"**{session_request['exercise'].title()} — "
                                f"Week {session_request['week_num']}**\n\n"
                                f"{formatted_week}"
                            ),
                        }

        else:
            if not re.search(r"\d", user_message):
                assistant_message = {
                    "role": "assistant",
                    "content": (
                        "I’m not sure what program information you want. "
                        "You can ask about a lift summary, a week, or a "
                        "specific session."
                    ),
                }

            else:
                try:
                    current_maxes = extract_maxes_with_groq(
                        user_message
                    )
                except Exception:
                    current_maxes = extract_maxes(user_message)

            if len(current_maxes) != 3:
                raise ValueError(
                    "Please provide squat, bench, and deadlift maxes."
                )

            # Keep the original values for display.
            displayed_maxes = current_maxes.copy()

            # Convert pounds to kilograms for the generator.
            if unit == "lb":
                current_maxes = {
                    lift: value * 0.453592
                    for lift, value in current_maxes.items()
                }

            st.session_state.pending_maxes = current_maxes
            st.session_state.pending_displayed_maxes = (
                displayed_maxes
            )
            st.session_state.pending_unit = unit

            assistant_message = {
                "role": "assistant",
                "content": (
                    f"Parsed maxes: "
                    f"Squat: {displayed_maxes['squat']:.1f} {unit}, "
                    f"Bench: {displayed_maxes['bench']:.1f} {unit}, "
                    f"Deadlift: "
                    f"{displayed_maxes['deadlift']:.1f} {unit}. "
                    f"Confirm below to generate the program."
                ),
            }

    except Exception as error:
        assistant_message = {
            "role": "assistant",
            "content": f"Request failed: `{error}`",
        }

    st.session_state.messages.append(assistant_message)
    st.rerun()

if st.session_state.get("pending_maxes") is not None:
    displayed_maxes = st.session_state.pending_displayed_maxes
    pending_unit = st.session_state.pending_unit

    st.info(
        f"Squat: {displayed_maxes['squat']:.1f} {pending_unit} | "
        f"Bench: {displayed_maxes['bench']:.1f} {pending_unit} | "
        f"Deadlift: {displayed_maxes['deadlift']:.1f} {pending_unit}"
    )

    button_col1, button_col2 = st.columns(2)

    with button_col1:
        generate_clicked = st.button(
            "Generate program",
            type="primary",
            use_container_width=True,
            key="generate_program_button",
        )

    with button_col2:
        edit_clicked = st.button(
            "Edit maxes",
            use_container_width=True,
            key="edit_maxes_button",
        )

    if edit_clicked:
        st.session_state.pending_maxes = None
        st.session_state.pending_displayed_maxes = None
        st.session_state.pending_unit = None
        st.rerun()

    if generate_clicked:
        try:
            program, grouped_program = generate_program(
                st.session_state.pending_maxes
            )

            if pending_unit == "lb":
                grouped_program = grouped_program.copy()

                grouped_program["prescription"] = (
                    grouped_program["num_sets"].astype(str)
                    + " x "
                    + grouped_program["reps"].astype(str)
                    + " @ "
                    + (
                        grouped_program["prescribed_weight_kg"]
                        / 0.453592
                    ).round(1).astype(str)
                    + " lb"
                )

            try:
                explanation = explain_program(
                    grouped_program,
                    displayed_maxes,
                    pending_unit,
                )
            except Exception:
                explanation = (
                    "Your program follows the stored SBD progression "
                    "and scales each prescription from your provided maxes."
    )

            st.session_state.generated_program = grouped_program

            st.session_state.messages.append(
            {
                "role": "assistant",
                "content": (
                    f"Your program is ready in {pending_unit}.\n\n"
                    f"{explanation}\n\n"
                    "Open a lift below to view its sessions."
                ),
                "program": grouped_program,
                "unit": pending_unit,
            }
)
            st.session_state.active_displayed_maxes = displayed_maxes
            st.session_state.active_unit = pending_unit
            st.session_state.pending_maxes = None
            st.session_state.pending_displayed_maxes = None
            st.session_state.pending_unit = None

            st.rerun()

        except Exception as error:
            st.error(f"Program generation failed: {error}")