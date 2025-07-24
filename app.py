import argparse
import base64
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


APP_MODES = ["practice", "exam", "key", "bookmark"]
SESSION_QUESTION_FILE = Path(parse_args().questions_file).absolute()


class CurrentQuestion:
    @property
    def index(self):
        return st.session_state.view_indices[st.session_state.current_view_pos]

    @property
    def data(self):
        return st.session_state.questions[self.index]

    @property
    def state(self):
        return st.session_state.question_states[self.index]

    @property
    def correct_answer(self):
        return self.state["correct_answer"]

    @property
    def user_answer(self):
        return self.state["user_answer"]

    @user_answer.setter
    def user_answer(self, answer):
        self.state["user_answer"] = answer

    @property
    def type(self):
        return self.state["type"]

    @property
    def is_correct(self):
        if self.type == "ordering":
            return self.user_answer == self.correct_answer
        else:
            return set(self.user_answer) == set(self.correct_answer)

    @property
    def available_options(self):
        return self.state["available_options"]


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


def question_mode(question):
    mode = question.get("type", "")
    if "single" in mode:
        return "single"
    elif "ordering" in mode:
        return "ordering"
    elif "multiple" in mode:
        return "multiple"
    else:
        raise ValueError("Question type mismatch")


def get_answers(question, question_type):
    if question_type == "ordering":
        return question.get("correct_order", [])
    else:
        return [
            option.get("id")
            for option in question["options"]
            if option.get("is_correct", False)
        ]


def get_options(question):
    options = [
        f"{option.get('id', '')}. {option.get('text', 'No text available')}"
        for option in question.get("options", [])
    ]
    return options


def init_questions_states():
    questions = load_questions(SESSION_QUESTION_FILE)
    random.shuffle(questions)
    st.session_state.questions = questions
    st.session_state.question_states = []
    st.session_state.key_indices = []
    for n, q in enumerate(questions):
        qtype = question_mode(q)
        is_key = qtype == "ordering"
        state = {
            "type": qtype,
            "answered": False,
            "bookmarked": False,
            "skipped": False,
            "key": is_key,
            "correct_answer": get_answers(q, qtype),
            "user_answer": None,
            "available_options": get_options(q),
        }
        st.session_state.question_states.append(state)
        if is_key:
            st.session_state.key_indices.append(n)
    st.session_state.n_key_questions = len(st.session_state.key_indices)
    st.session_state.current_view_pos = 0


def switch_mode(mode, exam_size=50):
    if "questions" not in st.session_state:
        return

    current_mode = st.session_state.get("mode")
    if current_mode == mode:
        return

    st.session_state.mode = mode
    st.session_state.current_view_pos = 0
    if st.session_state.mode == "practice":
        st.session_state.n_questions = len(st.session_state.questions)
        st.session_state.view_indices = list(range(st.session_state.n_questions))
    elif st.session_state.mode == "exam":
        st.session_state.view_indices = get_n_questions(exam_size)
        st.session_state.n_questions = exam_size
        for i in st.session_state.view_indices:
            st.session_state.question_states[i]["answered"] = False
            st.session_state.question_states[i]["skipped"] = False
        st.session_state.exam_start_time = datetime.now()
        st.session_state.exam_end_time = None
    elif st.session_state.mode == "key":
        st.session_state.view_indices = st.session_state.key_indices
        st.session_state.n_questions = len(st.session_state.key_indices)
    elif st.session_state.mode == "bookmark":
        st.session_state.view_indices = st.session_state.bookmarked
        st.session_state.n_questions = len(st.session_state.bookmarked)
    else:
        raise ValueError("Unknown mode")
    reset_answers()


def set_default_mode():
    """Redundant for readibility."""
    if not st.session_state.get("mode"):
        switch_mode("practice")


def is_exam_mode():
    return st.session_state.mode == "exam"


def initialize_session_state():
    """Initialize streamlit session state.

    Returns early if already initialized.
    Runs fully upon start and reset.
    """
    if st.session_state.get("has_initialized"):
        return

    # Load questions, shuffle and set default mode
    init_questions_states()
    set_default_mode()

    # Initialize view position
    st.session_state.current_question = CurrentQuestion()

    # Exam mode
    st.session_state.exam_start_time = datetime.now() if is_exam_mode() else None
    st.session_state.exam_end_time = None

    # Special modes
    st.session_state.bookmarked = []
    st.session_state.skipped = set()

    # Answers, navigation and progress trackers
    st.session_state.count_correct_answers = 0
    st.session_state.count_total_answered = 0
    st.session_state.selected_options = None
    st.session_state.quiz_completed = False

    st.session_state.show_results_popup = False
    st.session_state.theme = "One Dark"

    # Set initialization
    st.session_state.has_initialized = True


def reset_quiz():
    """
    Reset the quiz to start over
    """
    st.session_state.has_initialized = False
    initialize_session_state()


def skip_question():
    """
    Skip the current question and mark it for later review
    """
    # Add current question index to skipped questions
    ind = st.session_state.current_view_pos
    st.session_state.skipped.add(ind)

    # Move to the next question
    next_question()


def reset_answers():
    if not st.session_state.get("has_initialized"):
        return
    st.session_state.current_question.state["answered"] = False
    st.session_state.current_question.user_answer = None
    st.session_state.selected_options = None


def toggle_key_questions():
    """
    Toggle between showing all questions and only key questions
    """
    mode = "key" if st.session_state.mode != "key" else "practice"
    switch_mode(mode)


def go_to_question(index):
    """
    Go to a specific question index
    """
    st.session_state.current_view_pos = index
    st.session_state.skipped.discard(index)
    reset_answers()


def next_question():
    """
    Move to the next question
    """
    n_questions = st.session_state.n_questions
    for i in range(st.session_state.current_view_pos + 1, n_questions):
        ind = st.session_state.view_indices[i]
        if st.session_state.question_states[ind]["answered"]:
            continue
        go_to_question(i)
        break
    else:
        if is_exam_mode():
            st.session_state.show_results_popup = True
        st.session_state.quiz_completed = True


def previous_question():
    """
    Move to the previous question
    """
    ind = st.session_state.current_view_pos
    for i in range(st.session_state.current_view_pos, -1, -1):
        ind = st.session_state.view_indices[i]
        if st.session_state.question_states[ind]["answered"]:
            continue
        go_to_question(i)
        break


def bookmark_question():
    """
    Bookmark the current question for later review
    """
    ind = st.session_state.current_question.index
    if ind not in st.session_state.bookmarked:
        st.session_state.bookmarked.append(ind)
        st.session_state.current_question.state["bookmarked"] = True
        st.success("Question bookmarked!")
    else:
        st.session_state.bookmarked.remove(ind)
        st.session_state.current_question.state["bookmarked"] = False
        st.info("Bookmark removed")


def toggle_bookmarked_questions():
    """
    Toggle between showing all questions and only bookmarked questions
    """
    mode = "bookmark" if st.session_state.mode != "bookmark" else "practice"
    switch_mode(mode)


def finish_quiz():
    """
    Finish the quiz early and show results
    """
    st.session_state.quiz_completed = True
    if (is_exam_mode()) and st.session_state.exam_end_time is None:
        st.session_state.exam_end_time = datetime.now()


def show_stopwatch_exam():
    """Live stopwatch for exam mode"""
    if is_exam_mode():
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
    with st.expander("See instructions", expanded=False):
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

    def handle_exam_toggle():
        if "exam_toggle" not in st.session_state:
            return
        new_mode = "exam" if st.session_state.exam_toggle else "practice"
        switch_mode(new_mode)

    # Show exam mode button
    exam_col, finish_col, _ = st.columns([1, 1, 3])
    with exam_col:
        st.toggle(
            "Exam mode",
            key="exam_toggle",
            value=is_exam_mode(),
            on_change=handle_exam_toggle,
            disabled=st.session_state.quiz_completed,
        )
    with finish_col:
        if not st.session_state.quiz_completed:
            st.button(
                "Finish Quiz",
                on_click=finish_quiz,
                type="primary",
            )
        else:
            # Button to restart the quiz
            st.button("Start Over", on_click=reset_quiz)

    # Navigation buttons
    col1, col2, _ = st.columns([1, 1, 3])
    with col1:
        # Key questions
        if st.session_state.mode == "key":
            label = "All Questions"
        else:
            label = "Key Questions"
        key = "toggle_key_questions_button"
        st.button(
            label,
            key=key,
            on_click=toggle_key_questions,
            disabled=is_exam_mode() or st.session_state.quiz_completed,
        )
    with col2:
        # Bookmarked questions
        if st.session_state.mode == "bookmark":
            label = "All Questions"
        else:
            label = "Bookmarked"
        key = "toggle_bookmarked_questions"
        disabled = False if st.session_state.bookmarked else True
        st.button(
            label, key=key, on_click=toggle_bookmarked_questions, disabled=disabled
        )


def check_questions(attr=None):
    attr = attr or "questions"
    if not st.session_state[attr]:
        st.error("No questions available. Please check the questions.json file.")


def render_bookmark_button():
    is_bookmarked = st.session_state.current_question.state["bookmarked"]
    icon = "🔖" if is_bookmarked else "📌"
    label = f"{icon} {'Remove Bookmark' if is_bookmarked else 'Bookmark'}"
    st.button(label, on_click=bookmark_question, disabled=is_exam_mode())


def display_skipped_questions():
    skipped_questions = st.session_state.skipped
    if not skipped_questions:
        return
    valid_mode = st.session_state.mode in ["practice", "exam"]
    if not valid_mode:
        return

    with st.expander(f"Skipped questions ({len(skipped_questions)})"):
        for n, ind in enumerate(skipped_questions):
            label = f"Question {ind + 1}"
            key = f"skipped_{n}"
            st.button(label, key=key, on_click=partial(go_to_question, ind))


def render_question():
    question_type = st.session_state.current_question.state["type"]
    # Display the question ID in small, subtle text
    st.caption(f"Question ID: {st.session_state.current_question.data['question_id']}")

    # Display if this is a key question
    if question_type == "ordering":
        st.info("⭐ Key Question ⭐")

    # Display the question itself
    question = st.session_state.current_question.data
    question_content = question.get("question", "No questions found.")
    st.subheader(question_content)

    # Get options from the question (handle both list and dictionary formats)
    options = question.get("options", [])
    if not options:
        st.warning("No options available for this questions.")

    st.session_state.selected_options = st.session_state.selected_options or []

    if not st.session_state.current_question.state["answered"]:
        if question_type == "ordering":
            render_ordering_question()
        else:
            render_multiple_choice_question()

        render_submit_skip_buttons(question_type)
    else:
        if question_type == "ordering":
            render_feedback_ordering()
        else:
            render_feedback_multiple_choice()
        render_general_feedback()
        render_navigation_buttons()


def swap_elements(a: list, i: int, j: int):
    a[i], a[j] = a[j], a[i]


def render_options_column():
    for n, option in enumerate(st.session_state.current_question.available_options):
        option_container = st.container()
        opt_cols = option_container.columns([8, 2])
        with opt_cols[0]:
            st.markdown(option)
        with opt_cols[1]:
            if st.button("Add →", key=f"add_{n}"):
                # Move option from available to selected
                # st.session_state.current_question.available_options.remove(option)
                st.session_state.selected_options.append(option)
                st.rerun()


def render_answer_column():
    if not st.session_state.selected_options:
        st.info("Add options from the left panel to build your answer")

    for i, option in enumerate(st.session_state.selected_options):
        answer_container = st.container()
        ans_cols = answer_container.columns([1, 6, 1, 1])
        # Swap question columns
        with ans_cols[0]:
            is_button_pressed = False
            if i > 0:
                is_button_pressed = st.button("↑", key=f"up_{i}")

            if is_button_pressed:
                swap_elements(st.session_state.selected_options, i, i - 1)
                st.rerun()

        with ans_cols[1]:
            st.markdown(option)
        # Down button
        with ans_cols[2]:
            is_button_pressed = False
            if i < len(st.session_state.selected_options) - 1:
                is_button_pressed = st.button("↓", key=f"down_{i}")

            if is_button_pressed:
                swap_elements(st.session_state.selected_options, i, i + 1)
                st.rerun()

        # Remove button
        with ans_cols[3]:
            if st.button("✕", key=f"remove_{i}"):
                # Move option from selected back to available
                st.session_state.selected_options.remove(option)
                st.session_state.current_question.available_options.append(option)
                st.rerun()

    # Clear all button
    if st.session_state.selected_options:
        if st.button("Clear all", key="clear_selected"):
            # Move all selected options back to available
            st.session_state.current_question.available_options.extend(
                st.session_state.selected_options
            )
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


def render_multiple_choice_question():
    current_question = st.session_state.current_question
    if current_question.type == "single":
        st.radio(
            "Select your answer:",
            current_question.available_options,
            index=None,
            key="selected_option",
            on_change=on_answer_selection,
        )
    elif current_question.type == "multiple":
        for option in current_question.available_options:
            st.checkbox(option, key=f"checkbox_{option[0]}", value=False)
    else:
        st.error("Wrong mode.")


def render_submit_skip_buttons(mode):
    col1, col2, col3 = st.columns([1, 1, 5])
    with col1:
        label = "Submit"
        disabled = st.session_state.current_question.user_answer is None
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


def disable_previous():
    for i in range(st.session_state.current_view_pos, -1, -1):
        ind = st.session_state.view_indices[i]
        if st.session_state.question_states[ind]["answered"]:
            continue
        else:
            break
    else:
        return True

    return False


def render_navigation_buttons():
    # Navigation buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
    with col1:
        st.button(
            "Previous",
            on_click=previous_question,
            disabled=disable_previous(),
        )
    with col2:
        st.button("Next", on_click=next_question)
    with col3:
        st.button("Retry", on_click=reset_answers, disabled=is_exam_mode())
    with col4:
        # Bookmark button - toggles bookmark status
        render_bookmark_button()


def render_feedback_ordering():
    st.write("Your order:")
    current_question = st.session_state.current_question
    options = {
        option["id"]: option["text"] for option in current_question.data["options"]
    }
    for option_id in current_question.user_answer:
        st.write(f"{option_id}. {options[option_id]}")

    if current_question.is_correct:
        st.success("Correct answer! ✅")
    else:
        st.error("Incorrect answer ❌")
        # Show the correct
        st.write("Correct order:")
        for option_id in current_question.correct_answer:
            st.success(f"{option_id}. {options[option_id]}")


def render_feedback_multiple_choice():
    # Display the user's answers
    st.write("Your answers:")
    # Convert to set for easy comparison
    current_question = st.session_state.current_question
    user_answers = set(current_question.user_answer)
    options = {
        option["id"]: (option["text"], option.get("explanation", ""))
        for option in current_question.data["options"]
    }
    correct_options = set(current_question.correct_answer)
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
        if current_question.is_correct:
            st.success("All correct options were selected!")
        else:
            st.error("At least partially wrong!")


def display_progress_bar():
    mode = st.session_state.get("mode")
    if mode not in APP_MODES:
        raise ValueError("Unknown mode.")

    n_questions = st.session_state.n_questions
    st.progress(st.session_state.current_view_pos / n_questions)
    st.write(f"Question {st.session_state.current_view_pos + 1} of {n_questions}")


def display_question():
    """
    Display the current question and its options
    """
    show_stopwatch_exam()
    check_questions()
    display_skipped_questions()
    display_progress_bar()
    render_question()


def render_general_feedback():
    feedback = st.session_state.current_question.data.get("feedback", "")
    if feedback:
        st.markdown(feedback)


def check_answer_ordering():
    # Consistency check for user answers
    if not _user_answer_exists():
        return

    if st.session_state.current_question.is_correct:
        st.session_state.count_correct_answers += 1
    st.session_state.count_total_answered += 1
    st.session_state.current_question.state["answered"] = True


def _user_answer_exists() -> bool:
    if st.session_state.current_question.user_answer is None:
        st.error("No user answer found.")
        return False
    else:
        return True


def check_answer_multiple_choice():
    # Consistency check for user answers
    if not _user_answer_exists():
        return

    if st.session_state.current_question.is_correct:
        st.session_state.count_correct_answers += 1

    st.session_state.count_total_answered += 1
    st.session_state.current_question.state["answered"] = True


def on_answer_selection():
    """
    Function to handle when a user selects an answer for single-choice questions
    """
    # Select 1st character and put in list
    st.session_state.current_question.user_answer = [
        st.session_state.selected_option[0]
    ]


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

    st.session_state.current_question.user_answer = selected_options
    check_answer_multiple_choice()


def handle_submit_ordering():
    """
    Handle the submission of a drag and drop ordering question
    """
    # Only use the selected options that were moved to the "Answer" side
    if "selected_options" in st.session_state:
        st.session_state.current_question.user_answer = [
            elt[0] for elt in st.session_state.selected_options
        ]
    else:
        st.session_state.current_question.user_answer = []

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

    if is_exam_mode():
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
        if st.session_state.bookmarked:
            st.subheader("Bookmarked Questions")
            st.write("You might want to review these questions:")
            for idx in st.session_state.bookmarked:
                try:
                    question = st.session_state.questions[idx]
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


def show_results_popup():
    """
    Show a popup asking if the user wants to see results
    """
    st.markdown("### Exam done")
    st.write("Get results?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            st.session_state.show_results_popup = False
            st.session_state.quiz_completed = True
            st.session_state.exam_end_time = datetime.now()
            st.rerun()
    with col2:
        if st.button("No"):
            st.session_state.show_results_popup = False
            st.rerun()


def main():
    """Run the application."""
    # Set page configuration
    st.set_page_config(page_title="Interactive Quiz", page_icon="❓", layout="centered")
    st.title("Interactive Quiz")

    # Initialize session state
    initialize_session_state()
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
