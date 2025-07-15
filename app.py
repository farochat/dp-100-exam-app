import base64
import copy
import io
import json
import random
from datetime import datetime

import matplotlib.pyplot as plt
import streamlit as st

# Set page configuration
st.set_page_config(page_title="Interactive Quiz", page_icon="❓", layout="centered")


# def get_n_questions(sample: int) -> list[int]:
#     n_questions = len(st.session_state.questions)
#     total = min(sample, n_questions)
#     return random.sample(range(n_questions), total)


# def switch_mode():
#     if st.session_state.exam_mode:
#         new_exam_state = {
#             "status": 0,
#             "start_time": None,
#             "end_time": None,
#             "content": None,
#         }
#         st.session_state.exam_state.update(new_exam_state)
#     elif st.session_state.app_state == "training":
#         new_exam_state = {
#             "status": 1,
#             "start_time": datetime.now(),
#             "end_time": None,
#             "content": get_n_questions(50),
#         }
#         st.session_state.exam_state.update(new_exam_state)
#     else:
#         st.error("Unknown state")

#     st.session_state.exam_mode = not st.session_state.exam_mode


# exam_mode = {"status": 0, "start_time": None, "end_time": None, "content": []}
# training_mode = {
#     "status": 0,
#     "key_questions": {"status": 0, "content": []},
#     "bookmarked_questions": {"status": 0, "content": []},
# }
# application_state = {
#     "mode": ["training", "exam"],
#     "status": [0, 1],
# }


def load_questions():
    """
    Load questions from the JSON file and return them as a list
    """
    try:
        with open("examtopics_question_1.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(
            "Error: questions.json file not found. Please make sure it exists in the root directory."
        )
        return []
    except json.JSONDecodeError:
        st.error("Error: Invalid JSON format in questions.json file.")
        return []
    except Exception as e:
        st.error(f"An error occurred while loading questions: {str(e)}")
        return []


def generate_random_order(n: int) -> list[int]:
    """Generate a random list of index."""
    ind = list(range(n))
    random.shuffle(ind)
    return ind


# def get_key_questions() -> list[int]:
#     """Return key questions index."""
#     key_question_indices = []

#     for i, question in enumerate(st.session_state.questions):
#         if question.get("type") in KEY_QUESTIONS:


# KEY_QUESTIONS = ["ordering", "drag_and_drop_ordering"]
# SESSION_STATE = {
#     "questions": load_questions(),
#     "question_order": generate_random_order(),
#     # "key_questions":
# }


# def init_session_state():
#     for attr, action in SESSION_STATE.items():
#         if attr in st.session_state:
#             continue
#         st.session_state[attr] = action


def initialize_session_state():
    """
    Initialize the session state variables if they don't exist
    """

    def init_if_missing(key, default):
        if key not in st.session_state:
            st.session_state[key] = default

    # questions should always exists, there's no point into having that dynamically set
    # Load question and setup order
    # TODO: question as data struct -> (json/data, metadata, order?)
    # in the end, order is just a single call and create a sense of randomness
    # What I think can help: question list, current_shuffled_index
    if "questions" not in st.session_state:
        st.session_state.questions = load_questions()

    n = len(st.session_state.questions)
    init_if_missing("question_order", generate_random_order(n))

    # Create a list of key questions (ordering type questions)
    # TODO: still wondering about the necessity of "Key Questions" feature
    if "key_questions" not in st.session_state:
        key_question_indices = []
        for i, question in enumerate(st.session_state.questions):
            if question.get("type") in ["ordering", "drag_and_drop_ordering"]:
                key_question_indices.append(i)
        st.session_state.key_questions = key_question_indices

    init_if_missing("current_question_index", 0)

    # Navigation and progress trackers
    init_if_missing("skipped_questions", [])
    init_if_missing("bookmarked_questions", [])
    init_if_missing("answered", False)
    init_if_missing("user_answer", None)
    init_if_missing("correct_answer", None)
    init_if_missing("is_correct", False)
    init_if_missing("count_correct_answers", 0)
    init_if_missing("count_total_answered", 0)
    init_if_missing("quiz_completed", False)

    # Track if we're viewing key questions
    # This feels redundant.
    init_if_missing("viewing_key_questions", False)
    init_if_missing("viewing_bookmarked_questions", False)

    # Display and settings
    # Theme selection
    init_if_missing("theme", "One Dark")
    init_if_missing("show_results_popup", False)

    # Exam mode
    init_if_missing("exam_mode", False)
    init_if_missing("exam_start_time", None)
    init_if_missing("exam_end_time", None)


def reset_states():
    # fresh counters
    st.session_state.current_question_index = 0
    st.session_state.answered = False
    st.session_state.user_answer = None
    st.session_state.correct_answer = None
    st.session_state.count_correct_answers = 0
    st.session_state.count_total_answered = 0
    st.session_state.quiz_completed = False
    st.session_state.viewing_key_questions = False
    st.session_state.viewing_bookmarked_questions = False
    st.session_state.show_results_popup = False


def start_exam_mode():
    """Kick off a 50-question timed exam."""
    # guard if bank < 50
    n = len(st.session_state.questions)
    total_q = min(50, n)
    st.session_state.question_order = random.sample(range(n), total_q)
    st.session_state.exam_mode = True
    st.session_state.exam_start_time = datetime.now()
    st.session_state.exam_end_time = None

    reset_states()


def reset_quiz():
    """
    Reset the quiz to start over
    """
    n = len(st.session_state.questions)
    st.session_state.question_order = generate_random_order(n)

    # Exam mode
    st.session_state.exam_mode = False
    st.session_state.exam_start_time = None
    st.session_state.exam_end_time = None

    reset_states()
    st.session_state.skipped_questions = []
    st.session_state.bookmarked_questions = []

    # Clear drag and drop state if it exists
    if "drag_drop_order" in st.session_state:
        del st.session_state.drag_drop_order
    if "available_options" in st.session_state:
        del st.session_state.available_options
    if "selected_options" in st.session_state:
        del st.session_state.selected_options


def skip_question():
    """
    Skip the current question and mark it for later review
    """
    # Add current question index to skipped questions if not already there
    # if skipped_question is a set:
    # ind = st.session_state.current_question_index
    # st.session_state.skipped_questions.add(ind)
    if (
        st.session_state.current_question_index
        not in st.session_state.skipped_questions
    ):
        st.session_state.skipped_questions.append(
            st.session_state.current_question_index
        )

    # Move to the next question
    next_question()


def toggle_key_questions():
    """
    Toggle between showing all questions and only key questions
    """
    st.session_state.viewing_key_questions = not st.session_state.viewing_key_questions
    st.session_state.viewing_bookmarked_questions = False
    st.session_state.current_question_index = 0
    st.session_state.answered = False
    st.session_state.user_answer = None
    st.session_state.correct_answer = None

    # Clear drag and drop state if it exists
    if "drag_drop_order" in st.session_state:
        del st.session_state.drag_drop_order
    if "available_options" in st.session_state:
        del st.session_state.available_options
    if "selected_options" in st.session_state:
        del st.session_state.selected_options


def go_to_question(index):
    """
    Go to a specific question index
    """
    st.session_state.current_question_index = index
    st.session_state.answered = False
    st.session_state.user_answer = None
    st.session_state.correct_answer = None

    # Clear drag and drop state if it exists
    if "drag_drop_order" in st.session_state:
        del st.session_state.drag_drop_order
    if "available_options" in st.session_state:
        del st.session_state.available_options
    if "selected_options" in st.session_state:
        del st.session_state.selected_options


def next_question():
    """
    Move to the next question
    """
    n_questions = len(st.session_state.question_order)
    if st.session_state.current_question_index < n_questions - 1:
        # Not finished
        st.session_state.current_question_index += 1
        st.session_state.answered = False
        st.session_state.user_answer = None

        # Clear drag and drop state when moving to a new question
        if "drag_drop_order" in st.session_state:
            del st.session_state.drag_drop_order
        if "available_options" in st.session_state:
            del st.session_state.available_options
        if "selected_options" in st.session_state:
            del st.session_state.selected_options
    else:
        # In exam mode, show results popup when all questions are answered
        if st.session_state.exam_mode:
            st.session_state.show_results_popup = True
        else:
            st.session_state.quiz_completed = True


def previous_question():
    """
    Move to the previous question
    """
    if st.session_state.current_question_index > 0:
        st.session_state.current_question_index -= 1
        st.session_state.answered = False
        st.session_state.user_answer = None

        # Clear drag and drop state when moving to a new question
        if "drag_drop_order" in st.session_state:
            del st.session_state.drag_drop_order
        if "available_options" in st.session_state:
            del st.session_state.available_options
        if "selected_options" in st.session_state:
            del st.session_state.selected_options


def get_current_question() -> dict:
    # Get the actual question index from the randomized order
    current_id = st.session_state.current_question_index
    question_id = st.session_state.question_order[current_id]
    return st.session_state.questions[question_id]


def bookmark_question():
    """
    Bookmark the current question for later review
    """
    if (
        st.session_state.current_question_index
        not in st.session_state.bookmarked_questions
    ):
        st.session_state.bookmarked_questions.append(
            st.session_state.current_question_index
        )
        st.success("Question bookmarked!")
    else:
        st.session_state.bookmarked_questions.remove(
            st.session_state.current_question_index
        )
        st.info("Bookmark removed")


def toggle_bookmarked_questions():
    """
    Toggle between showing all questions and only bookmarked questions
    """
    st.session_state.viewing_bookmarked_questions = (
        not st.session_state.viewing_bookmarked_questions
    )
    st.session_state.viewing_key_questions = False
    st.session_state.current_question_index = 0
    st.session_state.answered = False
    st.session_state.user_answer = None

    # Clear drag and drop state if it exists
    if "drag_drop_order" in st.session_state:
        del st.session_state.drag_drop_order
    if "available_options" in st.session_state:
        del st.session_state.available_options
    if "selected_options" in st.session_state:
        del st.session_state.selected_options


def get_theme_css(theme_name):
    """
    Return CSS for the selected theme
    """
    themes = {
        "One Dark": {
            "bg": "#282c34",
            "text": "#abb2bf",
            "button_bg": "#3b4048",
            "button_text": "#e5c07b",
            "button_border": "#528bff",
            "hover_bg": "#3e4451",
            "hover_text": "#98c379",
            "hover_border": "#56b6c2",
            "heading": "#61afef",
            "progress": "#98c379",
            "radio_bg": "#353b45",
            "success_bg": "rgba(152, 195, 121, 0.2)",
            "success_text": "#98c379",
            "success_border": "#98c379",
            "info_bg": "rgba(97, 175, 239, 0.2)",
            "info_text": "#61afef",
            "info_border": "#61afef",
            "warning_bg": "rgba(229, 192, 123, 0.2)",
            "warning_text": "#e5c07b",
            "warning_border": "#e5c07b",
            "error_bg": "rgba(224, 108, 117, 0.2)",
            "error_text": "#e06c75",
            "error_border": "#e06c75",
        },
        "Solarized Dark": {
            "bg": "#002b36",
            "text": "#839496",
            "button_bg": "#073642",
            "button_text": "#b58900",
            "button_border": "#268bd2",
            "hover_bg": "#073642",
            "hover_text": "#2aa198",
            "hover_border": "#859900",
            "heading": "#268bd2",
            "progress": "#859900",
            "radio_bg": "#073642",
            "success_bg": "rgba(133, 153, 0, 0.2)",
            "success_text": "#859900",
            "success_border": "#859900",
            "info_bg": "rgba(38, 139, 210, 0.2)",
            "info_text": "#268bd2",
            "info_border": "#268bd2",
            "warning_bg": "rgba(181, 137, 0, 0.2)",
            "warning_text": "#b58900",
            "warning_border": "#b58900",
            "error_bg": "rgba(220, 50, 47, 0.2)",
            "error_text": "#dc322f",
            "error_border": "#dc322f",
        },
        "Monokai": {
            "bg": "#272822",
            "text": "#f8f8f2",
            "button_bg": "#3e3d32",
            "button_text": "#e6db74",
            "button_border": "#66d9ef",
            "hover_bg": "#49483e",
            "hover_text": "#a6e22e",
            "hover_border": "#fd971f",
            "heading": "#66d9ef",
            "progress": "#a6e22e",
            "radio_bg": "#3e3d32",
            "success_bg": "rgba(166, 226, 46, 0.2)",
            "success_text": "#a6e22e",
            "success_border": "#a6e22e",
            "info_bg": "rgba(102, 217, 239, 0.2)",
            "info_text": "#66d9ef",
            "info_border": "#66d9ef",
            "warning_bg": "rgba(230, 219, 116, 0.2)",
            "warning_text": "#e6db74",
            "warning_border": "#e6db74",
            "error_bg": "rgba(249, 38, 114, 0.2)",
            "error_text": "#f92672",
            "error_border": "#f92672",
        },
        "Dracula": {
            "bg": "#282a36",
            "text": "#f8f8f2",
            "button_bg": "#44475a",
            "button_text": "#f1fa8c",
            "button_border": "#8be9fd",
            "hover_bg": "#44475a",
            "hover_text": "#50fa7b",
            "hover_border": "#ff79c6",
            "heading": "#8be9fd",
            "progress": "#50fa7b",
            "radio_bg": "#44475a",
            "success_bg": "rgba(80, 250, 123, 0.2)",
            "success_text": "#50fa7b",
            "success_border": "#50fa7b",
            "info_bg": "rgba(139, 233, 253, 0.2)",
            "info_text": "#8be9fd",
            "info_border": "#8be9fd",
            "warning_bg": "rgba(241, 250, 140, 0.2)",
            "warning_text": "#f1fa8c",
            "warning_border": "#f1fa8c",
            "error_bg": "rgba(255, 85, 85, 0.2)",
            "error_text": "#ff5555",
            "error_border": "#ff5555",
        },
        "Nord": {
            "bg": "#2e3440",
            "text": "#d8dee9",
            "button_bg": "#3b4252",
            "button_text": "#ebcb8b",
            "button_border": "#88c0d0",
            "hover_bg": "#434c5e",
            "hover_text": "#a3be8c",
            "hover_border": "#81a1c1",
            "heading": "#88c0d0",
            "progress": "#a3be8c",
            "radio_bg": "#3b4252",
            "success_bg": "rgba(163, 190, 140, 0.2)",
            "success_text": "#a3be8c",
            "success_border": "#a3be8c",
            "info_bg": "rgba(136, 192, 208, 0.2)",
            "info_text": "#88c0d0",
            "info_border": "#88c0d0",
            "warning_bg": "rgba(235, 203, 139, 0.2)",
            "warning_text": "#ebcb8b",
            "warning_border": "#ebcb8b",
            "error_bg": "rgba(191, 97, 106, 0.2)",
            "error_text": "#bf616a",
            "error_border": "#bf616a",
        },
    }

    theme = themes.get(theme_name, themes["One Dark"])

    css = f"""
    <style>
    .stApp {{
        background-color: {theme["bg"]};
        color: {theme["text"]};
    }}
    .stButton>button {{
        background-color: {theme["button_bg"]};
        color: {theme["button_text"]};
        border: 1px solid {theme["button_border"]};
    }}
    .stButton>button:hover {{
        background-color: {theme["hover_bg"]};
        color: {theme["hover_text"]};
        border: 1px solid {theme["hover_border"]};
    }}
    .stMarkdown {{
        color: {theme["text"]};
    }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {theme["heading"]};
    }}
    .stProgress > div > div {{
        background-color: {theme["progress"]};
    }}
    .stRadio > div {{
        background-color: {theme["radio_bg"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stSuccess {{
        background-color: {theme["success_bg"]};
        color: {theme["success_text"]};
        border: 1px solid {theme["success_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stInfo {{
        background-color: {theme["info_bg"]};
        color: {theme["info_text"]};
        border: 1px solid {theme["info_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stWarning {{
        background-color: {theme["warning_bg"]};
        color: {theme["warning_text"]};
        border: 1px solid {theme["warning_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    .stError {{
        background-color: {theme["error_bg"]};
        color: {theme["error_text"]};
        border: 1px solid {theme["error_border"]};
        border-radius: 5px;
        padding: 10px;
    }}
    </style>
    """

    return css


def finish_quiz():
    """
    Finish the quiz early and show results
    """
    st.session_state.quiz_completed = True
    if st.session_state.exam_mode and st.session_state.exam_end_time is None:
        st.session_state.exam_end_time = datetime.now()


def show_stopwatch_exam():
    """Live stopwatch for exam mode"""
    if st.session_state.exam_mode and st.session_state.exam_start_time:
        elapsed = datetime.now() - st.session_state.exam_start_time
        minutes, seconds = divmod(int(elapsed.total_seconds()), 60)
        st.markdown(f"⏱️ **Time Elapsed:** {minutes:02d}:{seconds:02d}")


def make_layout():
    # Apply the selected theme CSS
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

    # Top bar with theme selection and finish button
    theme_col, _ = st.columns([1, 4])

    with theme_col:
        themes = ["One Dark", "Solarized Dark", "Monokai", "Dracula", "Nord"]
        selected_theme = st.selectbox(
            "Select Theme", themes, index=themes.index(st.session_state.theme)
        )
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
    # Add a message about navigating questions
    st.markdown(
        """
        ### Instructions:
        - You can **skip** questions and return to them later.
        - Use the **Key Questions** button to see only the ordering questions.
        - Use the **Bookmarked** button to see questions you've bookmarked.
        - **Bookmark** important questions for later review.
        - Navigate with the **Previous** and **Next** buttons.
        - You can **retry** questions you have already answered.
        - After completing the quiz, you can **download your results**.
        """
    )
    # Show exam mode button
    exam_col, _, finish_col = st.columns([2, 2, 1])
    with exam_col:
        st.button("🎯 Exam Mode (50 questions)", on_click=start_exam_mode)
    with finish_col:
        st.button("Finish Quiz", on_click=finish_quiz, type="primary")

    # Navigation buttons
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        # Key questions
        if st.session_state.viewing_key_questions:
            label = "All Questions"
        else:
            label = "Key Questions"
        key = "toggle_key_questions_button"
        st.button(label, key=key, on_click=toggle_key_questions)
    with col2:
        # Bookmarked questions
        if st.session_state.viewing_bookmarked_questions:
            label = "All Questions"
        else:
            label = "Bookmarked"
        key = "toggle_bookmarked_questions"
        st.button(label, key=key, on_click=toggle_bookmarked_questions)


def check_questions(attr=None):
    attr = attr or "questions"
    if not st.session_state[attr]:
        st.error("No questions available. Please check the questions.json file.")


def render_bookmark_button():
    is_bookmarked = (
        st.session_state.current_question_index in st.session_state.bookmarked_questions
    )
    icon = "🔖" if is_bookmarked else "📌"
    label = f"{icon} {'Remove Bookmark' if is_bookmarked else 'Bookmark'}"
    st.button(label, on_click=bookmark_question)


def get_questions_info() -> tuple:
    """Returns question id and max number of questions."""
    # If viewing key questions, use the key_questions list
    if st.session_state.viewing_key_questions:
        if not st.session_state.key_questions:
            st.warning("No key questions (drag and drop type) available.")
            st.session_state.viewing_key_questions = False
            return

        # Check if current index is valid for key questions
        if st.session_state.current_question_index >= len(
            st.session_state.key_questions
        ):
            st.session_state.current_question_index = 0

        # Get the real question index from key_questions
        real_idx = st.session_state.key_questions[
            st.session_state.current_question_index
        ]
        question_idx = real_idx
        max_questions = len(st.session_state.key_questions)
    elif st.session_state.viewing_bookmarked_questions:
        if not st.session_state.bookmarked_questions:
            st.warning("No bookmarked questions available.")
            st.session_state.viewing_bookmarked_questions = False
            return

        # Check if current index is valid for bookmarked questions
        if st.session_state.current_question_index >= len(
            st.session_state.bookmarked_questions
        ):
            st.session_state.current_question_index = 0

        # Get the real question index from bookmarked_questions
        real_idx = st.session_state.bookmarked_questions[
            st.session_state.current_question_index
        ]
        question_idx = st.session_state.question_order[real_idx]
        max_questions = len(st.session_state.bookmarked_questions)
    else:
        # Normal mode - get question from randomized order
        if st.session_state.current_question_index >= len(
            st.session_state.question_order
        ):
            # In exam mode, show results popup when all questions are answered
            if st.session_state.exam_mode:
                st.session_state.show_results_popup = True
                return
            else:
                st.session_state.quiz_completed = True
                return

        question_idx = st.session_state.question_order[
            st.session_state.current_question_index
        ]
        max_questions = len(st.session_state.question_order)
    return st.session_state.questions[question_idx], question_idx, max_questions


def display_skipped_questions():
    valid_state = (
        st.session_state.skipped_questions
        and not st.session_state.viewing_key_questions
        and not st.session_state.viewing_bookmarked_questions
    )
    if valid_state:
        with st.expander(
            f"Skipped Questions ({len(st.session_state.skipped_questions)})"
        ):
            for i, idx in enumerate(st.session_state.skipped_questions):
                if st.button(f"Go to Question {idx + 1}", key=f"skipped_{i}"):
                    go_to_question(idx)


def render_question(question):
    mode = question.get("type", "")
    if "single" in mode:
        mode = "single"
    elif "ordering" in mode:
        mode = "ordering"
    elif "multiple" in mode:
        mode = "multiple"
    else:
        st.error("Mode error.")

    if mode == "ordering":
        render_ordering_question()
    else:
        render_multiple_choice_question(mode)

    render_bottom_buttons(mode)


def swap_elements(a: list, i: int, j: int):
    a[i], a[j] = a[j], a[i]


def render_options_column():
    for option in st.session_state.available_options:
        option_id = option.get("id")
        option_text = option.get("text", "No text available")
        option_container = st.container()
        opt_cols = option_container.columns([8, 2])
        with opt_cols[0]:
            st.markdown(f"**{option_id}.** {option_text}")
        with opt_cols[1]:
            if st.button("Add →", key=f"add_{option_id}"):
                # Move option from available to selected
                st.session_state.available_options.remove(option)
                st.session_state.selected_options.append(option)
                st.rerun()


def render_answer_column():
    if not st.session_state.selected_options:
        st.info("Add options from the left panel to build your answer")

    for i, option in enumerate(st.session_state.selected_options):
        option_id = option.get("id")
        option_text = option.get("text", "No text available")
        answer_container = st.container()
        ans_cols = answer_container.columns([1, 6, 1, 1])
        # Swap question columns
        with ans_cols[0]:
            is_button_pressed = False
            if i > 0:
                is_button_pressed = st.button("↑", key=f"up_{option_id}")

            if is_button_pressed:
                swap_elements(st.session_state.selected_options, i, i - 1)
                st.rerun()

        with ans_cols[1]:
            st.markdown(f"**{option_id}.** {option_text}")
        # Down button
        with ans_cols[2]:
            is_button_pressed = False
            if i < len(st.session_state.selected_options) - 1:
                is_button_pressed = st.button("↓", key=f"down_{option_id}")

            if is_button_pressed:
                swap_elements(st.session_state.selected_options, i, i + 1)
                st.rerun()

        # Remove button
        with ans_cols[3]:
            if st.button("✕", key=f"remove_{option_id}"):
                # Move option from selected back to available
                st.session_state.selected_options.remove(option)
                st.session_state.available_options.append(option)
                st.rerun()

    # Clear all button
    if st.session_state.selected_options:
        if st.button("Clear all", key="clear_selected"):
            # Move all selected options back to available
            st.session_state.available_options.extend(st.session_state.selected_options)
            st.session_state.selected_options = []
            st.rerun()


def render_ordering_question():
    # Create two columns for the "Options" and "Answer" panels
    if not st.session_state.answered:
        st.info("Select options and arrange them in the correct order")
        left_col, right_col = st.columns(2)

        # Left panel - Available options
        with left_col:
            st.markdown("### Options")
            render_options_column()

        # Right panel - Selected options (answer)
        with right_col:
            st.markdown("### Answer")
            render_answer_column()
    else:
        pass


def render_multiple_choice_question(mode):
    # Display instructions
    if mode == "single":
        pass
    elif mode == "multiple":
        st.info("Select all correct answers (multiple selections allowed).")
    else:
        st.error("Wrong mode.")

    # Create checkboxes for each option
    labels = []
    for option in st.session_state.available_options:
        option_id = option.get("id", "")
        option_text = option.get("text", "No text available")

        # Create a checkbox
        label = f"{option_id}. {option_text}"
        labels.append(label)
        if mode == "multiple":
            st.checkbox(label, key=f"checkbox_{option_id}", value=False)

    if labels and mode == "single":
        st.radio(
            "Select your answer:",
            labels,
            index=None,
            key="selected_option",
            on_change=on_answer_selection,
        )


def render_bottom_buttons(mode):
    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        label = "Submit"
        if mode == "multiple":
            st.button(label, on_click=on_multiple_answer_selection)
        elif mode == "single":
            st.button(
                label,
                on_click=check_answer,
                disabled=st.session_state.user_answer is None,
            )
        elif mode == "ordering":
            st.button(label, on_click=handle_submit_ordering)
        else:
            st.error("Mode error.")
            raise ValueError("Mode error")
    with col2:
        st.button("Skip", key="skip_button", on_click=skip_question)
    with col3:
        # Bookmark button - toggles bookmark status
        render_bookmark_button()


def display_question():
    """
    Display the current question and its options
    """
    show_stopwatch_exam()
    check_questions()

    # Get question infos depending on state (bookmark, key, etc...)
    _, question_idx, max_questions = get_questions_info()
    # Get the current question
    current_question = st.session_state.questions[question_idx]

    # Show skipped questions
    display_skipped_questions()

    # Display progress
    st.progress((st.session_state.current_question_index) / max_questions)
    st.write(
        f"Question {st.session_state.current_question_index + 1} of {max_questions}"
    )
    # Display the question ID in small, subtle text
    st.caption(f"Question ID: {question_idx}")

    ###TODO: THIS IS WHERE IT SHOULD BE SPLIT
    # Display if this is a key question
    if current_question.get("type") in ["ordering", "drag_and_drop_ordering"]:
        st.info("⭐ Key Question ⭐")

    # Display the question itself
    question_content = current_question.get("question", "No questions found.")
    st.subheader(question_content)

    # Get options from the question (handle both list and dictionary formats)
    options = current_question.get("options", [])
    if not options:
        st.warning("No options available for this questions.")

    if "available_options" not in st.session_state:
        st.session_state.available_options = copy.deepcopy(options)
    if "selected_options" not in st.session_state:
        st.session_state.selected_options = []

    if not st.session_state.answered:
        # Different UI based on question type
        render_question(current_question)

    # If the question has been answered, show the feedback
    # TODO: why is this part of display_question? better to use answer no?
    else:
        user_choice = st.session_state.user_answer

        # Different feedback based on question type
        if current_question.get("type") in ["ordering", "drag_and_drop_ordering"]:
            render_feedback_ordering()

        elif current_question.get("type") == "multiple_choice_multiple_answer":
            # Display the user's answers
            st.write("Your answers:")

            # Convert to set for easy comparison, ensure it's a list first
            user_answers = set(
                user_choice if isinstance(user_choice, list) else [user_choice]
            )

            # Get all correct option IDs
            correct_options = [
                option.get("id")
                for option in options
                if option.get("is_correct", False)
            ]

            # Show each option and whether it was correct or not
            for option in options:
                option_id = option.get("id", "Unknown")
                option_text = option.get("text", "Unknown option")

                is_correct = option.get("is_correct", False)
                was_selected = option_id in user_answers

                # Four possible states:
                # 1. Correct and selected (Good)
                # 2. Correct but not selected (Missed)
                # 3. Incorrect but selected (Wrong)
                # 4. Incorrect and not selected (Good)

                if is_correct and was_selected:
                    st.success(f"{option_id}. {option_text} ✅ (Correct)")
                elif is_correct and not was_selected:
                    st.warning(
                        f"{option_id}. {option_text} ❗ (Missed this correct answer)"
                    )
                elif not is_correct and was_selected:
                    st.error(f"{option_id}. {option_text} ❌ (Incorrect)")
                else:
                    # Not correct and not selected - good to skip
                    st.write(f"{option_id}. {option_text} (Not selected - correct)")

                # Display explanation if available for this option
                if option.get("explanation"):
                    st.info(f"Explanation: {option.get('explanation')}")

            # Overall correctness
            if user_answers and user_answers == set(correct_options):
                st.success(
                    "Your answer is completely correct! All correct options were selected."
                )
            else:
                st.error(
                    "Your answer is not completely correct. You either missed some correct options or selected some incorrect ones."
                )

        else:  # Single choice or true/false questions
            try:
                correct_option = next(
                    (option for option in options if option.get("is_correct", False)),
                    None,
                )

                for option in options:
                    option_id = option.get("id", "Unknown")
                    option_text = option.get("text", "Unknown option")

                    if option_id == user_choice:
                        if option.get("is_correct", False):
                            st.success(f"{option_id}. {option_text} ✅")
                        else:
                            st.error(f"{option_id}. {option_text} ❌")

                        if option.get("explanation"):
                            st.info(f"Explanation: {option.get('explanation')}")
                    elif option.get("is_correct", False):
                        st.success(f"{option_id}. {option_text} (Correct Answer)")
                        if user_choice != option_id and option.get("explanation"):
                            st.info(f"Explanation: {option.get('explanation')}")
                    else:
                        st.write(f"{option_id}. {option_text}")
            except Exception as e:
                st.error(f"Error displaying answer feedback: {str(e)}")

        st.write("---")
        # Check if feedback exists in the question data
        if "feedback" in current_question:
            st.write(f"**Feedback:** {current_question.get('feedback', '')}")

        # Navigation buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
        with col1:
            st.button(
                "Previous",
                on_click=previous_question,
                disabled=st.session_state.current_question_index == 0,
            )
        with col2:
            st.button("Next", on_click=next_question)
        with col3:
            st.button(
                "Retry", on_click=lambda: setattr(st.session_state, "answered", False)
            )
        with col4:
            # Bookmark button - toggles bookmark status
            render_bookmark_button()


def check_answer_ordering():
    # Consistency check for user answers
    if not _user_answer_exists():
        return

    current_question, *_ = get_questions_info()
    st.session_state.correct_answer = current_question.get("correct_order", [])

    # Render feedback and get user answer
    user_answer = [option.get("id") for option in st.session_state.user_answer]
    is_correct = user_answer == st.session_state.correct_answer
    st.session_state.correct_answer = st.session_state.correct_answer
    if is_correct:
        st.session_state.count_correct_answers += 1
    st.session_state.is_correct = is_correct
    st.session_state.answered = True
    st.session_state.count_total_answered += 1


def render_feedback_ordering():
    st.write("Your order:")
    for option in st.session_state.user_answer:
        option_id = option.get("id")
        option_text = option.get("text", "Unknown option")
        st.write(f"{option_id}. {option_text}")

    if st.session_state.is_correct:
        st.success("Correct answer! ✅")
    else:
        st.error("Incorrect answer ❌")
        # Show the correct
        st.write("Correct order:")
        question, *_ = get_questions_info()
        options = {option["id"]: option["text"] for option in question["options"]}
        for option_id in st.session_state.correct_answer:
            option_text = options[option_id]
            st.success(f"{option_id}. {option_text}")


def _user_answer_exists() -> bool:
    if st.session_state.user_answer is None:
        st.error("No user answer found.")
        return False
    else:
        return True


def check_answer():
    """
    Check if the selected answer is correct and update the session state
    """
    if st.session_state.user_answer is not None:
        # Get the actual question index from the randomized order
        current_question = get_current_question()

        # Handle different question types
        # TODO: drag and drop does not necessarily requires ordering
        if current_question["type"] in ["ordering", "drag_and_drop_ordering"]:
            # For ordering questions, check if the order matches the correct order
            answer = current_question.get("correct_order", [])
            user_answer = [option.get("id") for option in st.session_state.user_answer]
            correct_answer = user_answer == answer
        elif current_question["type"] == "multiple_choice_multiple_answer":
            # For multiple choice with multiple correct answers
            # Get all correct option IDs
            correct_options = [
                option.get("id")
                for option in current_question.get("options", [])
                if option.get("is_correct", False)
            ]

            # Check if user's answer matches all correct options (set comparison)
            user_answer = set(
                st.session_state.user_answer
                if isinstance(st.session_state.user_answer, list)
                else [st.session_state.user_answer]
            )
            if user_answer:
                correct_answer = user_answer == set(correct_options)
            else:
                correct_answer = False

        else:
            correct_option = [
                f"{option.get('id')}. {option.get('text')}"
                for option in current_question.get("options", [])
                if option.get("is_correct", False)
            ]
            if not correct_option:
                st.error("No correct option.")

            if len(correct_option) > 1:
                st.warning("More than one correct option when there should be only one")

            correct_option = correct_option[0]
            correct_answer = correct_option == st.session_state.user_answer

        st.session_state.count_total_answered += 1
        st.session_state.answered = True
        if correct_answer:
            st.session_state.count_correct_answers += 1


def on_answer_selection():
    """
    Function to handle when a user selects an answer for single-choice questions
    """
    st.session_state.user_answer = st.session_state.selected_option


def on_multiple_answer_selection():
    """
    Function to handle when a user selects answers for multiple-choice questions
    """
    # Get all selected checkboxes (options where value is True)
    selected_options = []
    for option_id, value in st.session_state.items():
        if option_id.startswith("checkbox_") and value:
            # Extract the option ID from the checkbox key (remove 'checkbox_' prefix)
            selected_options.append(option_id.replace("checkbox_", ""))

    st.session_state.user_answer = selected_options
    check_answer()


def handle_submit_ordering():
    """
    Handle the submission of a drag and drop ordering question
    """
    # Only use the selected options that were moved to the "Answer" side
    if "selected_options" in st.session_state:
        st.session_state.user_answer = st.session_state.selected_options
    else:
        st.session_state.user_answer = []

    # Call check_answer to evaluate the submission and show feedback
    check_answer_ordering()


def create_donut_chart():
    """
    Create a donut chart showing the correct vs. incorrect answers
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("none")  # Transparent background for the figure

    # Data
    count_correct = st.session_state.count_correct_answers
    count_incorrect = st.session_state.count_total_answered - count_correct
    remaining_questions = (
        len(st.session_state.question_order) - st.session_state.count_total_answered
    )

    # Data for the pie chart
    sizes = [count_correct, count_incorrect, remaining_questions]
    labels = ["Correct", "Incorrect", "Unanswered"]
    colors = ["#4CAF50", "#F44336", "#9E9E9E"]

    # Create a donut chart
    _, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"width": 0.4, "edgecolor": "w"},
    )

    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis("equal")
    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.setp(texts, size=12)

    # Title in the center
    ax.text(
        0,
        0,
        f"{count_correct}/{st.session_state.count_total_answered}",
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
    )

    # Add a subtitle
    ax.text(0, -0.12, "Score", ha="center", va="center", fontsize=12)

    # Return the figure
    return fig


def get_chart_as_base64(fig):
    """
    Convert matplotlib figure to base64 string for embedding in HTML
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    return img_str


def download_results():
    """
    Generate and download a summary of the quiz results
    """
    # Create donut chart
    fig = create_donut_chart()
    img_str = get_chart_as_base64(fig)

    # Data for the report
    count_correct = st.session_state.count_correct_answers
    count_incorrect = st.session_state.count_total_answered - count_correct
    remaining_questions = (
        len(st.session_state.question_order) - st.session_state.count_total_answered
    )
    success_rate = (
        (count_correct / st.session_state.count_total_answered * 100)
        if st.session_state.count_total_answered > 0
        else 0
    )

    # Create HTML report
    html = f"""
    <html>
    <head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .results {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
        }}
        .stat-box {{
            text-align: center;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background-color: #f8f8f8;
            width: 20%;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .stat-label {{
            font-size: 14px;
            color: #666;
        }}
        .chart {{
            text-align: center;
            margin: 20px 0;
        }}
        h1 {{
            color: #2c3e50;
        }}
        h2 {{
            color: #3498db;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            font-size: 12px;
            color: #999;
        }}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Quiz Results Summary</h1>
                <p>Generated on {st.session_state.get("date_completed", "Not completed")}</p>
            </div>

            <h2>Performance Overview</h2>
            <div class="results">
                <div class="stat-box">
                    <div class="stat-value">{count_correct}</div>
                    <div class="stat-label">Correct</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{count_incorrect}</div>
                    <div class="stat-label">Incorrect</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{remaining_questions}</div>
                    <div class="stat-label">Unanswered</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{success_rate:.1f}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>

            <div class="chart">
                <img src="data:image/png;base64,{img_str}" alt="Quiz Results Chart" width="400">
            </div>

            <h2>Summary</h2>
            <p>You answered {st.session_state.count_total_answered} out of {len(st.session_state.question_order)} total questions.</p>
            <p>Your success rate is {success_rate:.1f}% based on the {st.session_state.count_total_answered} questions you answered.</p>

            <div class="footer">
                <p>This report was generated by Interactive Quiz Application</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Return the HTML for downloading
    return html


def display_results():
    """
    Display the final results of the quiz
    """
    st.title("Quiz Completed!")

    # Set the completion date if not already set
    if "date_completed" not in st.session_state:
        st.session_state.date_completed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Calculate the percentage based on answered questions only
    total_questions = len(st.session_state.question_order)
    correct_answers = st.session_state.correct_answers
    total_answered = st.session_state.count_total_answered
    unanswered = total_questions - total_answered

    # Calculate percentage based on questions answered, not total questions
    percentage = (correct_answers / total_answered * 100) if total_answered > 0 else 0

    if (
        st.session_state.exam_mode
        and st.session_state.exam_start_time
        and st.session_state.exam_end_time
    ):
        total_secs = int(
            (
                st.session_state.exam_end_time - st.session_state.exam_start_time
            ).total_seconds()
        )
        mm, ss = divmod(total_secs, 60)
        st.metric("⏱️ Time taken", f"{mm} min {ss} sec")

    # Create layout with columns
    col1, col2 = st.columns([2, 2])

    with col1:
        st.header(f"Your Score: {correct_answers}/{total_answered} ({percentage:.1f}%)")

        # Progress bar for visual representation
        st.progress(percentage / 100)
        st.caption(
            f"Based on {total_answered} questions answered out of {total_questions} total questions"
        )

        # Display a different message based on the score
        if percentage >= 80:
            st.balloons()
            st.success("Great job! You have excellent knowledge!")
        elif percentage >= 60:
            st.info("Good work! Keep learning and improving!")
        else:
            st.warning("You might want to review the material and try again.")

        # Show bookmarked questions if any
        if st.session_state.bookmarked_questions:
            st.subheader("Bookmarked Questions")
            st.write("You might want to review these questions:")
            for idx in st.session_state.bookmarked_questions:
                try:
                    question_idx = st.session_state.question_order[idx]
                    question = st.session_state.questions[question_idx]
                    st.write(f"- {question.get('question', 'Unknown question')}")
                except Exception as e:
                    st.warning(f"Could not load bookmarked question: {str(e)}")

        # Statistics
        st.subheader("Quiz Statistics")
        stats_col1, stats_col2 = st.columns(2)
        with stats_col1:
            st.metric(label="Correct Answers", value=f"{correct_answers}")
            st.metric(label="Total Questions", value=f"{total_questions}")
        with stats_col2:
            st.metric(label="Questions Answered", value=f"{total_answered}")
            st.metric(label="Unanswered Questions", value=f"{unanswered}")

    with col2:
        # Display donut chart
        st.subheader("Performance Summary")
        fig = create_donut_chart()
        st.pyplot(fig)

        # Download button for results
        html_results = download_results()
        st.download_button(
            label="Download Results Report",
            data=html_results,
            file_name="quiz_results.html",
            mime="text/html",
        )

    # Button to restart the quiz
    st.button("Start Over", on_click=reset_quiz)


def show_results_popup():
    """
    Show a popup asking if the user wants to see results
    """
    # Create a popup container
    popup = st.container()
    popup.markdown(
        """
        <style>
        .popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            z-index: 1000;
            width: 300px;
        }
        .popup-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 999;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Show the popup content
    popup.markdown("<div class='popup-overlay'></div>", unsafe_allow_html=True)
    with popup:
        st.markdown("<div class='popup'>", unsafe_allow_html=True)
        st.markdown("### Has finalizado el examen")
        st.write("¿Deseas ver los resultados?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Sí"):
                st.session_state.show_results_popup = False
                st.session_state.quiz_completed = True
                st.session_state.exam_end_time = datetime.now()
                st.rerun()
        with col2:
            if st.button("No"):
                st.session_state.show_results_popup = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def main():
    """
    Main function to run the application
    """
    st.title("Interactive Quiz")

    # Initialize session state
    initialize_session_state()

    # Check if there are questions available
    if not st.session_state.questions:
        return

    make_layout()

    # Show results popup if needed
    if st.session_state.show_results_popup:
        show_results_popup()
        return

    # Check if the quiz is completed
    if st.session_state.quiz_completed:
        display_results()
    else:
        display_question()


if __name__ == "__main__":
    main()
