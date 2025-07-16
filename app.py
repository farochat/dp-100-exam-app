import argparse
import base64
import copy
import io
import json
import random
from datetime import datetime
from functools import partial
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from themes import get_theme_css, get_themes_list


def parse_args():
    """Parse arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--questions", dest="questions_file", type=str, default="questions.json"
    )
    return parser.parse_args()


def get_n_questions(sample: int = 50) -> list[int]:
    """Return a sample out of question index list."""
    total = min(sample, st.session_state.n_questions)
    return random.sample(range(st.session_state.n_questions), total)


def generate_random_order(n: int) -> list[int]:
    """Generate a random list of index."""
    ind = list(range(n))
    random.shuffle(ind)
    return ind


def load_questions(questions_file):
    """
    Load questions from the JSON file and return them as a list
    """
    try:
        with open(questions_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error(f"Error: file {questions_file} not found.")
        return []
    except json.JSONDecodeError:
        st.error(f"Error: invalid JSON format in {questions_file} file.")
        return []
    except Exception as e:
        st.error(f"An error occurred while loading questions: {str(e)}")
        return []


def initialize_session_state(args):
    """
    Initialize the session state variables if they don't exist
    """

    def init_if_missing(key, default):
        if key not in st.session_state:
            st.session_state[key] = default

    if "questions" not in st.session_state:
        questions_file = Path(args.questions_file).absolute()
        questions = load_questions(questions_file)
        # Shuffle questions and set session states
        random.shuffle(questions)
        st.session_state.questions = questions
        st.session_state.n_questions = len(questions)
        st.session_state.current_question_index = 0

    # Create a list of key questions (ordering type questions)
    if "key_questions" not in st.session_state:
        # Used to be based on pre-shuffled question order
        key_question_indices = []
        for i, question in enumerate(st.session_state.questions):
            if question.get("type") in ["ordering", "drag_and_drop_ordering"]:
                key_question_indices.append(i)
        st.session_state.key_questions = key_question_indices

    # Navigation and progress trackers
    init_if_missing("skipped_questions", set())
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
    st.session_state.exam_questions = random.sample(range(n), total_q)
    st.session_state.exam_questions = get_n_questions(50)
    st.session_state.exam_mode = True
    st.session_state.exam_start_time = datetime.now()
    st.session_state.exam_end_time = None

    reset_states()


def reset_quiz():
    """
    Reset the quiz to start over
    """
    random.shuffle(st.session_state.questions)
    # Create a list of key questions (ordering type questions)
    if "key_questions" not in st.session_state:
        # Used to be based on pre-shuffled question order
        key_question_indices = []
        for i, question in enumerate(st.session_state.questions):
            if question.get("type") in ["ordering", "drag_and_drop_ordering"]:
                key_question_indices.append(i)
        st.session_state.key_questions = key_question_indices

    # Exam mode
    st.session_state.exam_mode = False
    st.session_state.exam_start_time = None
    st.session_state.exam_end_time = None

    reset_states()
    st.session_state.skipped_questions = set()
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
    # Add current question index to skipped questions
    ind = st.session_state.current_question_index
    st.session_state.skipped_questions.add(ind)

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
    st.session_state.skipped_questions.discard(index)
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
    n_questions = st.session_state.n_questions
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
        themes = get_themes_list()
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
        max_questions = len(st.session_state.key_questions)
        if st.session_state.current_question_index >= max_questions:
            st.session_state.current_question_index = 0
        current_index = st.session_state.current_question_index
        question_idx = st.session_state.key_questions[current_index]
    elif st.session_state.viewing_bookmarked_questions:
        if not st.session_state.bookmarked_questions:
            st.warning("No bookmarked questions available.")
            st.session_state.viewing_bookmarked_questions = False
            return

        # Check if current index is valid for bookmarked questions
        max_questions = len(st.session_state.bookmarked_questions)
        if st.session_state.current_question_index >= max_questions:
            st.session_state.current_question_index = 0

        # Get the real question index from bookmarked_questions
        current_index = st.session_state.current_question_index
        question_idx = st.session_state.bookmarked_questions[current_index]
    else:
        # Normal mode - get question from randomized order
        max_questions = st.session_state.n_questions
        if st.session_state.current_question_index >= max_questions:
            # In exam mode, show results popup when all questions are answered
            if st.session_state.exam_mode:
                st.session_state.show_results_popup = True
                return
            else:
                st.session_state.quiz_completed = True
                return
        question_idx = st.session_state.current_question_index

    return st.session_state.questions[question_idx], question_idx, max_questions


def display_skipped_questions():
    skipped_questions = st.session_state.skipped_questions
    valid_state = (
        skipped_questions
        and not st.session_state.viewing_key_questions
        and not st.session_state.viewing_bookmarked_questions
    )
    if not valid_state:
        return

    with st.expander(f"Skipped questions ({len(skipped_questions)})"):
        for n, ind in enumerate(skipped_questions):
            label = f"Question {ind + 1}"
            key = f"skipped_{n}"
            st.button(label, key=key, on_click=partial(go_to_question, ind))


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

    if not st.session_state.answered:
        if mode == "ordering":
            render_ordering_question()
        else:
            render_multiple_choice_question(mode)

        render_submit_skip_buttons(mode)
    else:
        if mode == "ordering":
            render_feedback_ordering()
        else:
            render_feedback_multiple_choice()
        # render_general_feedback()
        st.write("---")
        # Check if feedback exists in the question data
        if "feedback" in question:
            st.write(f"**Feedback:** {question.get('feedback', '')}")
        render_navigation_buttons()


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


def render_submit_skip_buttons(mode):
    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        label = "Submit"
        disabled = st.session_state.user_answer is None
        if mode == "ordering":
            st.button(label, on_click=handle_submit_ordering)
        elif mode == "multiple":
            st.button(label, on_click=on_multiple_answer_selection)
        elif mode == "single":
            st.button(label, on_click=check_answer_multiple_choice, disabled=disabled)
        else:
            st.error("Mode error.")
            raise ValueError("Mode error")
    with col2:
        st.button("Skip", key="skip_button", on_click=skip_question)
    with col3:
        # Bookmark button - toggles bookmark status
        render_bookmark_button()


def render_navigation_buttons():
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


def render_feedback_multiple_choice():
    # Display the user's answers
    st.write("Your answers:")
    current_question, *_ = get_questions_info()
    # Convert to set for easy comparison, ensure it's a list first
    if isinstance(st.session_state.user_answer, list):
        user_answers = set(st.session_state.user_answer)
    else:
        user_answers = set(st.session_state.user_answer[0])

    options = {
        option["id"]: (option["text"], option.get("explanation", ""))
        for option in current_question["options"]
    }
    correct_options = set(st.session_state.correct_answer)
    wrong_options = set(options).difference(correct_options)
    missed_answers = correct_options.difference(user_answers)
    wrong_answers = wrong_options.intersection(user_answers)
    correct_answers = correct_options.intersection(user_answers)
    for option_id, (option_text, explanation) in options.items():
        text = f"{option_id}. {option_text}"
        if option_id in correct_answers:
            st.success(text + " ✅")
        elif option_id in wrong_answers:
            st.error(text + " ❌")
        else:
            if len(correct_options) > 1:
                if option_id in missed_answers:
                    st.warning(text + "❗ (Missed this correct answer)")
                else:
                    st.write(text + " (Not selected - correct)")
            else:
                st.write(text)

        # Display explanation if available for this option
        if explanation:
            st.info(f"Explanation: {explanation}")

    # Overall correctness
    if len(correct_options) > 1:
        if st.session_state.is_correct:
            st.success("All correct options were selected!")
        else:
            st.error("At least partially wrong!")


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
    st.caption(f"Question ID: {current_question['question_id']}")

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

    render_question(current_question)


def render_general_feedback():
    pass


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


def _user_answer_exists() -> bool:
    if st.session_state.user_answer is None:
        st.error("No user answer found.")
        return False
    else:
        return True


def check_answer_multiple_choice():
    # Consistency check for user answers
    if not _user_answer_exists():
        return

    # For multiple choice with multiple correct answers
    # Get all correct option IDs
    current_question, *_ = get_questions_info()
    st.session_state.correct_answer = [
        option.get("id")
        for option in current_question.get("options", [])
        if option.get("is_correct", False)
    ]

    # Check if user's answer matches all correct options (set comparison)
    if isinstance(st.session_state.user_answer, str):
        user_answer = [st.session_state.user_answer[0]]
        is_correct = user_answer == st.session_state.correct_answer
    elif isinstance(st.session_state.user_answer, list):
        is_correct = set(st.session_state.user_answer) == set(
            st.session_state.correct_answer
        )
    else:
        raise TypeError("Unexpected type for user answer.")

    st.session_state.is_correct = is_correct
    if is_correct:
        st.session_state.count_correct_answers += 1

    st.session_state.count_total_answered += 1
    st.session_state.answered = True


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
    check_answer_multiple_choice()


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
        st.session_state.n_questions - st.session_state.count_total_answered
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
        st.session_state.n_questions - st.session_state.count_total_answered
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
            <p>You answered {st.session_state.count_total_answered} out of {st.session_state.n_questions} total questions.</p>
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
    total_questions = st.session_state.n_questions
    correct_answers = st.session_state.count_correct_answers
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
            f"Based on {total_answered} answers out of {total_questions} questions"
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


def main(args):
    """
    Main function to run the application
    """
    # Set page configuration
    st.set_page_config(page_title="Interactive Quiz", page_icon="❓", layout="centered")
    st.title("Interactive Quiz")
    # Initialize session state
    initialize_session_state(args)

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
    main(parse_args())
