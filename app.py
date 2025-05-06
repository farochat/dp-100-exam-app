import streamlit as st
import json
import os
import matplotlib.pyplot as plt
import io
import base64

# Set page configuration
st.set_page_config(
    page_title="Interactive Quiz",
    page_icon="❓",
    layout="centered"
)

def load_questions():
    """
    Load questions from the JSON file and return them as a list
    """
    try:
        with open('questions.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("Error: questions.json file not found. Please make sure it exists in the root directory.")
        return []
    except json.JSONDecodeError:
        st.error("Error: Invalid JSON format in questions.json file.")
        return []
    except Exception as e:
        st.error(f"An error occurred while loading questions: {str(e)}")
        return []

def initialize_session_state():
    """
    Initialize the session state variables if they don't exist
    """
    if 'questions' not in st.session_state:
        st.session_state.questions = load_questions()
    
    # Generate random question order
    if 'question_order' not in st.session_state:
        import random
        # Create a list of indices and shuffle them
        indices = list(range(len(st.session_state.questions)))
        random.shuffle(indices)
        st.session_state.question_order = indices
    
    # Create a list of key questions (ordering type questions)
    if 'key_questions' not in st.session_state:
        key_question_indices = []
        for i, question in enumerate(st.session_state.questions):
            if question.get('type') in ['ordering', 'drag_and_drop_ordering']:
                key_question_indices.append(i)
        st.session_state.key_questions = key_question_indices
    
    # Track skipped questions
    if 'skipped_questions' not in st.session_state:
        st.session_state.skipped_questions = []
    
    # Track bookmarked questions
    if 'bookmarked_questions' not in st.session_state:
        st.session_state.bookmarked_questions = []
    
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    
    if 'answered' not in st.session_state:
        st.session_state.answered = False
    
    if 'user_answer' not in st.session_state:
        st.session_state.user_answer = None
    
    if 'correct_answers' not in st.session_state:
        st.session_state.correct_answers = 0
    
    if 'total_answered' not in st.session_state:
        st.session_state.total_answered = 0
    
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
        
    # Track if we're viewing key questions
    if 'viewing_key_questions' not in st.session_state:
        st.session_state.viewing_key_questions = False
        
    # Track if we're viewing bookmarked questions
    if 'viewing_bookmarked_questions' not in st.session_state:
        st.session_state.viewing_bookmarked_questions = False
        
    # Theme selection
    if 'theme' not in st.session_state:
        st.session_state.theme = 'One Dark'  # Default theme

def reset_quiz():
    """
    Reset the quiz to start over
    """
    # Regenerate random question order
    import random
    indices = list(range(len(st.session_state.questions)))
    random.shuffle(indices)
    st.session_state.question_order = indices
    
    st.session_state.current_question_index = 0
    st.session_state.answered = False
    st.session_state.user_answer = None
    st.session_state.correct_answers = 0
    st.session_state.total_answered = 0
    st.session_state.quiz_completed = False
    st.session_state.viewing_key_questions = False
    st.session_state.skipped_questions = []
    st.session_state.bookmarked_questions = []
    st.session_state.viewing_bookmarked_questions = False
    
    # Clear drag and drop state if it exists
    if 'drag_drop_order' in st.session_state:
        del st.session_state.drag_drop_order
    if 'available_options' in st.session_state:
        del st.session_state.available_options
    if 'selected_options' in st.session_state:
        del st.session_state.selected_options
        
def skip_question():
    """
    Skip the current question and mark it for later review
    """
    # Add current question index to skipped questions if not already there
    if st.session_state.current_question_index not in st.session_state.skipped_questions:
        st.session_state.skipped_questions.append(st.session_state.current_question_index)
    
    # Move to the next question
    next_question()
    
def toggle_key_questions():
    """
    Toggle between showing all questions and only key questions
    """
    st.session_state.viewing_key_questions = not st.session_state.viewing_key_questions
    st.session_state.current_question_index = 0
    st.session_state.answered = False
    st.session_state.user_answer = None
    
    # Clear drag and drop state if it exists
    if 'drag_drop_order' in st.session_state:
        del st.session_state.drag_drop_order
    if 'available_options' in st.session_state:
        del st.session_state.available_options
    if 'selected_options' in st.session_state:
        del st.session_state.selected_options
        
def go_to_question(index):
    """
    Go to a specific question index
    """
    st.session_state.current_question_index = index
    st.session_state.answered = False
    st.session_state.user_answer = None
    
    # Clear drag and drop state if it exists
    if 'drag_drop_order' in st.session_state:
        del st.session_state.drag_drop_order
    if 'available_options' in st.session_state:
        del st.session_state.available_options
    if 'selected_options' in st.session_state:
        del st.session_state.selected_options

def next_question():
    """
    Move to the next question
    """
    if st.session_state.current_question_index < len(st.session_state.questions) - 1:
        st.session_state.current_question_index += 1
        st.session_state.answered = False
        st.session_state.user_answer = None
        
        # Clear drag and drop state when moving to a new question
        if 'drag_drop_order' in st.session_state:
            del st.session_state.drag_drop_order
        if 'available_options' in st.session_state:
            del st.session_state.available_options
        if 'selected_options' in st.session_state:
            del st.session_state.selected_options
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
        if 'drag_drop_order' in st.session_state:
            del st.session_state.drag_drop_order
        if 'available_options' in st.session_state:
            del st.session_state.available_options
        if 'selected_options' in st.session_state:
            del st.session_state.selected_options

def check_answer():
    """
    Check if the selected answer is correct and update the session state
    """
    if st.session_state.user_answer is not None:
        # Get the actual question index from the randomized order
        question_idx = st.session_state.question_order[st.session_state.current_question_index]
        current_question = st.session_state.questions[question_idx]
        
        # Handle different question types
        if current_question['type'] in ['ordering', 'drag_and_drop_ordering']:
            # For ordering questions, check if the order matches the correct order
            if st.session_state.user_answer == current_question.get('correct_order', []):
                st.session_state.correct_answers += 1
        elif current_question['type'] == 'multiple_choice_multiple_answer':
            # For multiple choice with multiple correct answers
            try:
                # Get all correct option IDs
                correct_options = [option.get('id') for option in current_question.get('options', []) 
                                  if option.get('is_correct', False)]
                
                # Check if user's answer matches all correct options (set comparison)
                user_answers = set(st.session_state.user_answer if isinstance(st.session_state.user_answer, list) else [st.session_state.user_answer])
                if user_answers and user_answers == set(correct_options):
                    st.session_state.correct_answers += 1
            except Exception as e:
                st.error(f"Error checking multiple answer: {str(e)}")
        else:
            # For single choice or true/false questions
            try:
                correct_option = next((option for option in current_question.get('options', []) 
                                      if option.get('is_correct', False)), None)
                if correct_option and st.session_state.user_answer == correct_option.get('id'):
                    st.session_state.correct_answers += 1
            except Exception as e:
                st.error(f"Error checking answer: {str(e)}")
        
        st.session_state.total_answered += 1
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
        if option_id.startswith('checkbox_') and value:
            # Extract the option ID from the checkbox key (remove 'checkbox_' prefix)
            selected_options.append(option_id.replace('checkbox_', ''))
    
    st.session_state.user_answer = selected_options
    
def handle_drag_drop_submit():
    """
    Handle the submission of a drag and drop ordering question
    """
    # Only use the selected options that were moved to the "Answer" side
    if 'selected_options' in st.session_state:
        st.session_state.user_answer = st.session_state.selected_options
    else:
        st.session_state.user_answer = []
    
    # Call check_answer to evaluate the submission and show feedback
    check_answer()
    
def bookmark_question():
    """
    Bookmark the current question for later review
    """
    if st.session_state.current_question_index not in st.session_state.bookmarked_questions:
        st.session_state.bookmarked_questions.append(st.session_state.current_question_index)
        st.success("Question bookmarked!")
    else:
        st.session_state.bookmarked_questions.remove(st.session_state.current_question_index)
        st.info("Bookmark removed")

def toggle_bookmarked_questions():
    """
    Toggle between showing all questions and only bookmarked questions
    """
    st.session_state.viewing_bookmarked_questions = not st.session_state.viewing_bookmarked_questions
    st.session_state.viewing_key_questions = False
    st.session_state.current_question_index = 0
    st.session_state.answered = False
    st.session_state.user_answer = None
    
    # Clear drag and drop state if it exists
    if 'drag_drop_order' in st.session_state:
        del st.session_state.drag_drop_order
    if 'available_options' in st.session_state:
        del st.session_state.available_options
    if 'selected_options' in st.session_state:
        del st.session_state.selected_options

def get_theme_css(theme_name):
    """
    Return CSS for the selected theme
    """
    themes = {
        'One Dark': {
            'bg': '#282c34',
            'text': '#abb2bf',
            'button_bg': '#3b4048',
            'button_text': '#e5c07b',
            'button_border': '#528bff',
            'hover_bg': '#3e4451',
            'hover_text': '#98c379',
            'hover_border': '#56b6c2',
            'heading': '#61afef',
            'progress': '#98c379',
            'radio_bg': '#353b45',
            'success_bg': 'rgba(152, 195, 121, 0.2)',
            'success_text': '#98c379',
            'success_border': '#98c379',
            'info_bg': 'rgba(97, 175, 239, 0.2)',
            'info_text': '#61afef',
            'info_border': '#61afef',
            'warning_bg': 'rgba(229, 192, 123, 0.2)',
            'warning_text': '#e5c07b',
            'warning_border': '#e5c07b',
            'error_bg': 'rgba(224, 108, 117, 0.2)',
            'error_text': '#e06c75',
            'error_border': '#e06c75'
        },
        'Solarized Dark': {
            'bg': '#002b36',
            'text': '#839496',
            'button_bg': '#073642',
            'button_text': '#b58900',
            'button_border': '#268bd2',
            'hover_bg': '#073642',
            'hover_text': '#2aa198',
            'hover_border': '#859900',
            'heading': '#268bd2',
            'progress': '#859900',
            'radio_bg': '#073642',
            'success_bg': 'rgba(133, 153, 0, 0.2)',
            'success_text': '#859900',
            'success_border': '#859900',
            'info_bg': 'rgba(38, 139, 210, 0.2)',
            'info_text': '#268bd2',
            'info_border': '#268bd2',
            'warning_bg': 'rgba(181, 137, 0, 0.2)',
            'warning_text': '#b58900',
            'warning_border': '#b58900',
            'error_bg': 'rgba(220, 50, 47, 0.2)',
            'error_text': '#dc322f',
            'error_border': '#dc322f'
        },
        'Monokai': {
            'bg': '#272822',
            'text': '#f8f8f2',
            'button_bg': '#3e3d32',
            'button_text': '#e6db74',
            'button_border': '#66d9ef',
            'hover_bg': '#49483e',
            'hover_text': '#a6e22e',
            'hover_border': '#fd971f',
            'heading': '#66d9ef',
            'progress': '#a6e22e',
            'radio_bg': '#3e3d32',
            'success_bg': 'rgba(166, 226, 46, 0.2)',
            'success_text': '#a6e22e',
            'success_border': '#a6e22e',
            'info_bg': 'rgba(102, 217, 239, 0.2)',
            'info_text': '#66d9ef',
            'info_border': '#66d9ef',
            'warning_bg': 'rgba(230, 219, 116, 0.2)',
            'warning_text': '#e6db74',
            'warning_border': '#e6db74',
            'error_bg': 'rgba(249, 38, 114, 0.2)',
            'error_text': '#f92672',
            'error_border': '#f92672'
        },
        'Dracula': {
            'bg': '#282a36',
            'text': '#f8f8f2',
            'button_bg': '#44475a',
            'button_text': '#f1fa8c',
            'button_border': '#8be9fd',
            'hover_bg': '#44475a',
            'hover_text': '#50fa7b',
            'hover_border': '#ff79c6',
            'heading': '#8be9fd',
            'progress': '#50fa7b',
            'radio_bg': '#44475a',
            'success_bg': 'rgba(80, 250, 123, 0.2)',
            'success_text': '#50fa7b',
            'success_border': '#50fa7b',
            'info_bg': 'rgba(139, 233, 253, 0.2)',
            'info_text': '#8be9fd',
            'info_border': '#8be9fd',
            'warning_bg': 'rgba(241, 250, 140, 0.2)',
            'warning_text': '#f1fa8c',
            'warning_border': '#f1fa8c',
            'error_bg': 'rgba(255, 85, 85, 0.2)',
            'error_text': '#ff5555',
            'error_border': '#ff5555'
        },
        'Nord': {
            'bg': '#2e3440',
            'text': '#d8dee9',
            'button_bg': '#3b4252',
            'button_text': '#ebcb8b',
            'button_border': '#88c0d0',
            'hover_bg': '#434c5e',
            'hover_text': '#a3be8c',
            'hover_border': '#81a1c1',
            'heading': '#88c0d0',
            'progress': '#a3be8c',
            'radio_bg': '#3b4252',
            'success_bg': 'rgba(163, 190, 140, 0.2)',
            'success_text': '#a3be8c',
            'success_border': '#a3be8c',
            'info_bg': 'rgba(136, 192, 208, 0.2)',
            'info_text': '#88c0d0',
            'info_border': '#88c0d0',
            'warning_bg': 'rgba(235, 203, 139, 0.2)',
            'warning_text': '#ebcb8b',
            'warning_border': '#ebcb8b',
            'error_bg': 'rgba(191, 97, 106, 0.2)',
            'error_text': '#bf616a',
            'error_border': '#bf616a'
        }
    }
    
    theme = themes.get(theme_name, themes['One Dark'])
    
    css = f"""
    <style>
    .stApp {{
        background-color: {theme['bg']};
        color: {theme['text']};
    }}
    .stButton>button {{
        background-color: {theme['button_bg']};
        color: {theme['button_text']};
        border: 1px solid {theme['button_border']};
    }}
    .stButton>button:hover {{
        background-color: {theme['hover_bg']};
        color: {theme['hover_text']};
        border: 1px solid {theme['hover_border']};
    }}
    .stMarkdown {{
        color: {theme['text']};
    }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {theme['heading']};
    }}
    .stProgress > div > div {{
        background-color: {theme['progress']};
    }}
    .stRadio > div {{
        background-color: {theme['radio_bg']};
        border-radius: 5px;
        padding: 10px;
    }}
    .stSuccess {{
        background-color: {theme['success_bg']};
        color: {theme['success_text']};
        border: 1px solid {theme['success_border']};
        border-radius: 5px;
        padding: 10px;
    }}
    .stInfo {{
        background-color: {theme['info_bg']};
        color: {theme['info_text']};
        border: 1px solid {theme['info_border']};
        border-radius: 5px;
        padding: 10px;
    }}
    .stWarning {{
        background-color: {theme['warning_bg']};
        color: {theme['warning_text']};
        border: 1px solid {theme['warning_border']};
        border-radius: 5px;
        padding: 10px;
    }}
    .stError {{
        background-color: {theme['error_bg']};
        color: {theme['error_text']};
        border: 1px solid {theme['error_border']};
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

def display_question():
    """
    Display the current question and its options
    """
    if not st.session_state.questions:
        st.error("No questions available. Please check the questions.json file.")
        return
    
    # Apply the selected theme CSS
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)
    
    # Top bar with theme selection and finish button
    theme_col, space_col, finish_col = st.columns([2, 3, 1])
    
    with theme_col:
        themes = ['One Dark', 'Solarized Dark', 'Monokai', 'Dracula', 'Nord']
        selected_theme = st.selectbox("Select Theme", themes, index=themes.index(st.session_state.theme))
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()
    
    with finish_col:
        st.button("Finish Quiz", on_click=finish_quiz, type="primary")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("Key Questions" if not st.session_state.viewing_key_questions else "All Questions",
                    key="toggle_key_questions"):
            toggle_key_questions()
    with col2:
        if st.button("Bookmarked" if not st.session_state.viewing_bookmarked_questions else "All Questions",
                   key="toggle_bookmarked"):
            toggle_bookmarked_questions()
    
    # If viewing key questions, use the key_questions list
    if st.session_state.viewing_key_questions:
        if not st.session_state.key_questions:
            st.warning("No key questions (drag and drop type) available.")
            st.session_state.viewing_key_questions = False
            return
        
        # Check if current index is valid for key questions
        if st.session_state.current_question_index >= len(st.session_state.key_questions):
            st.session_state.current_question_index = 0
        
        # Get the real question index from key_questions
        real_idx = st.session_state.key_questions[st.session_state.current_question_index]
        question_idx = real_idx
        max_questions = len(st.session_state.key_questions)
    else:
        # Normal mode - get question from randomized order
        if st.session_state.current_question_index >= len(st.session_state.questions):
            st.session_state.quiz_completed = True
            return
        
        question_idx = st.session_state.question_order[st.session_state.current_question_index]
        max_questions = len(st.session_state.questions)
    
    # Get the current question
    current_question = st.session_state.questions[question_idx]
    
    # Show skipped questions
    if st.session_state.skipped_questions and not st.session_state.viewing_key_questions:
        with st.expander(f"Skipped Questions ({len(st.session_state.skipped_questions)})"):
            for i, idx in enumerate(st.session_state.skipped_questions):
                if st.button(f"Go to Question {idx + 1}", key=f"skipped_{i}"):
                    go_to_question(idx)
    
    # Display progress
    st.progress((st.session_state.current_question_index) / max_questions)
    st.write(f"Question {st.session_state.current_question_index + 1} of {max_questions}")
    
    # Display if this is a key question
    if current_question.get('type') in ['ordering', 'drag_and_drop_ordering']:
        st.info("⭐ Key Question ⭐")
    
    # Display the question
    st.subheader(current_question.get('question', 'Question unavailable'))
    
    # Get options from the question (handle both list and dictionary formats)
    if 'options' in current_question:
        options = current_question['options']
        
        # For true/false questions, only show options A and B if needed
        if current_question.get('type') == 'true_false' and len(options) > 2:
            options = options[:2]  # Only take the first two options (A and B)
    else:
        options = []
        st.warning("No options available for this question.")
    
    # If the question hasn't been answered yet, show the options
    if not st.session_state.answered:
        # Different UI based on question type
        if current_question.get('type') in ['ordering', 'drag_and_drop_ordering']:
            st.write("Arrange the options in the correct order:")
            
            # Initialize session state variables for the two-panel interface
            if 'available_options' not in st.session_state:
                st.session_state.available_options = [option.get('id') for option in options]
            if 'selected_options' not in st.session_state:
                st.session_state.selected_options = []
            
            # Create two columns for the "Options" and "Answer" panels
            st.write("Select options and arrange them in the correct order:")
            left_col, right_col = st.columns(2)
            
            # Left panel - Available options
            with left_col:
                st.markdown("### Options")
                for option_id in st.session_state.available_options:
                    try:
                        option_text = next((option.get('text', 'No text available') 
                                          for option in options if option.get('id') == option_id), 
                                          'Option text unavailable')
                        option_container = st.container()
                        opt_cols = option_container.columns([8, 2])
                        
                        with opt_cols[0]:
                            st.markdown(f"**{option_id}.** {option_text}")
                        
                        with opt_cols[1]:
                            if st.button("Add →", key=f"add_{option_id}"):
                                # Move option from available to selected
                                st.session_state.available_options.remove(option_id)
                                st.session_state.selected_options.append(option_id)
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error displaying option {option_id}: {str(e)}")
            
            # Right panel - Selected options (answer)
            with right_col:
                st.markdown("### Answer")
                if not st.session_state.selected_options:
                    st.info("Add options from the left panel to build your answer")
                
                for i, option_id in enumerate(st.session_state.selected_options):
                    try:
                        option_text = next((option.get('text', 'No text available') 
                                          for option in options if option.get('id') == option_id), 
                                          'Option text unavailable')
                        answer_container = st.container()
                        ans_cols = answer_container.columns([1, 6, 1, 1])
                        
                        # Up button
                        with ans_cols[0]:
                            if i > 0:  # Cannot move first item up
                                if st.button("↑", key=f"up_{option_id}"):
                                    # Swap this item with the one above it
                                    st.session_state.selected_options[i], st.session_state.selected_options[i-1] = \
                                        st.session_state.selected_options[i-1], st.session_state.selected_options[i]
                                    st.rerun()
                        
                        # Option text
                        with ans_cols[1]:
                            st.markdown(f"**{option_id}.** {option_text}")
                        
                        # Down button
                        with ans_cols[2]:
                            if i < len(st.session_state.selected_options) - 1:  # Cannot move last item down
                                if st.button("↓", key=f"down_{option_id}"):
                                    # Swap this item with the one below it
                                    st.session_state.selected_options[i], st.session_state.selected_options[i+1] = \
                                        st.session_state.selected_options[i+1], st.session_state.selected_options[i]
                                    st.rerun()
                        
                        # Remove button
                        with ans_cols[3]:
                            if st.button("✕", key=f"remove_{option_id}"):
                                # Move option from selected back to available
                                st.session_state.selected_options.remove(option_id)
                                st.session_state.available_options.append(option_id)
                                st.rerun()
                    except Exception as e:
                        st.error(f"Error displaying selected option {option_id}: {str(e)}")
                
                # Clear all button
                if st.session_state.selected_options:
                    if st.button("Clear all", key="clear_selected"):
                        # Move all selected options back to available
                        st.session_state.available_options.extend(st.session_state.selected_options)
                        st.session_state.selected_options = []
                        st.rerun()
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                st.button("Submit Order", on_click=handle_drag_drop_submit)
            with col2:
                st.button("Skip", on_click=skip_question)
            with col3:
                # Bookmark button - toggles bookmark status
                is_bookmarked = st.session_state.current_question_index in st.session_state.bookmarked_questions
                bookmark_icon = "🔖" if is_bookmarked else "📌"
                button_text = f"{bookmark_icon} {'Remove Bookmark' if is_bookmarked else 'Bookmark'}"
                st.button(button_text, on_click=bookmark_question)
        
        elif current_question.get('type') == 'multiple_choice_multiple_answer':
            # Display instruction for multiple answers
            st.info("Select all correct answers (multiple selections allowed).")
            
            # Create checkboxes for each option
            for option in options:
                option_id = option.get('id', 'Unknown')
                option_text = option.get('text', 'No text available')
                checkbox_key = f"checkbox_{option_id}"
                
                # Create a checkbox for each option
                st.checkbox(
                    f"{option_id}. {option_text}",
                    key=checkbox_key,
                    value=False
                )
            
            # Submit button for multiple choice
            col1, col2, col3 = st.columns([1, 1, 5])
            with col1:
                if st.button("Submit", key="submit_multiple", on_click=on_multiple_answer_selection):
                    check_answer()
            with col2:
                st.button("Skip", key="skip_multiple", on_click=skip_question)
        
        else:  # Single choice or true/false questions
            try:
                # Create a dictionary of option labels
                option_labels = {}
                for option in options:
                    if isinstance(option, dict) and 'id' in option and 'text' in option:
                        option_labels[option['id']] = f"{option['id']}. {option['text']}"
                
                # Set the key dynamically to avoid component reuse warning when navigating
                radio_key = f"q{st.session_state.current_question_index}_radio"
                
                if option_labels:
                    st.radio(
                        "Select your answer:",
                        options=list(option_labels.keys()),
                        format_func=lambda x: option_labels.get(x, x),
                        key='selected_option',
                        on_change=on_answer_selection,
                        index=None
                    )
                    
                    col1, col2, col3 = st.columns([1, 1, 5])
                    with col1:
                        st.button("Submit", on_click=check_answer, disabled=st.session_state.user_answer is None)
                    with col2:
                        st.button("Skip", on_click=skip_question)
                else:
                    st.error("No valid options found for this question.")
                    st.button("Skip", on_click=skip_question)
            except Exception as e:
                st.error(f"Error displaying question options: {str(e)}")
                st.button("Skip", on_click=skip_question)
        
    # If the question has been answered, show the feedback
    else:
        user_choice = st.session_state.user_answer
        
        # Different feedback based on question type
        if current_question.get('type') in ['ordering', 'drag_and_drop_ordering']:
            # Display the user's answer
            st.write("Your order:")
            for idx in user_choice:
                try:
                    option_text = next((option.get('text', 'Unknown option') for option in options if option.get('id') == idx), 'Unknown option')
                    st.write(f"{idx}. {option_text}")
                except Exception:
                    st.write(f"{idx}. Option unavailable")
            
            # Check if correct and show feedback
            if 'correct_order' in current_question and user_choice == current_question.get('correct_order', []):
                st.success("Correct answer! ✅")
            else:
                st.error("Incorrect answer ❌")
                
                # Show the correct order if available
                if 'correct_order' in current_question:
                    st.write("Correct order:")
                    for idx in current_question.get('correct_order', []):
                        try:
                            option_text = next((option.get('text', 'Unknown option') for option in options if option.get('id') == idx), 'Unknown option')
                            st.success(f"{idx}. {option_text}")
                        except Exception:
                            st.success(f"{idx}. Option unavailable")
                            
        elif current_question.get('type') == 'multiple_choice_multiple_answer':
            # Display the user's answers
            st.write("Your answers:")
            
            # Convert to set for easy comparison, ensure it's a list first
            user_answers = set(user_choice if isinstance(user_choice, list) else [user_choice])
            
            # Get all correct option IDs
            correct_options = [option.get('id') for option in options if option.get('is_correct', False)]
            
            # Show each option and whether it was correct or not
            for option in options:
                option_id = option.get('id', 'Unknown')
                option_text = option.get('text', 'Unknown option')
                
                is_correct = option.get('is_correct', False)
                was_selected = option_id in user_answers
                
                # Four possible states:
                # 1. Correct and selected (Good)
                # 2. Correct but not selected (Missed)
                # 3. Incorrect but selected (Wrong)
                # 4. Incorrect and not selected (Good)
                
                if is_correct and was_selected:
                    st.success(f"{option_id}. {option_text} ✅ (Correct)")
                elif is_correct and not was_selected:
                    st.warning(f"{option_id}. {option_text} ❗ (Missed this correct answer)")
                elif not is_correct and was_selected:
                    st.error(f"{option_id}. {option_text} ❌ (Incorrect)")
                else:
                    # Not correct and not selected - good to skip
                    st.write(f"{option_id}. {option_text} (Not selected - correct)")
                
                # Display explanation if available for this option
                if option.get('explanation'):
                    st.info(f"Explanation: {option.get('explanation')}")
            
            # Overall correctness
            if user_answers and user_answers == set(correct_options):
                st.success("Your answer is completely correct! All correct options were selected.")
            else:
                st.error("Your answer is not completely correct. You either missed some correct options or selected some incorrect ones.")
        
        else:  # Single choice or true/false questions
            try:
                correct_option = next((option for option in options if option.get('is_correct', False)), None)
                
                for option in options:
                    option_id = option.get('id', 'Unknown')
                    option_text = option.get('text', 'Unknown option')
                    
                    if option_id == user_choice:
                        if option.get('is_correct', False):
                            st.success(f"{option_id}. {option_text} ✅")
                        else:
                            st.error(f"{option_id}. {option_text} ❌")
                        
                        if option.get('explanation'):
                            st.info(f"Explanation: {option.get('explanation')}")
                    elif option.get('is_correct', False):
                        st.success(f"{option_id}. {option_text} (Correct Answer)")
                        if user_choice != option_id and option.get('explanation'):
                            st.info(f"Explanation: {option.get('explanation')}")
                    else:
                        st.write(f"{option_id}. {option_text}")
            except Exception as e:
                st.error(f"Error displaying answer feedback: {str(e)}")
        
        st.write("---")
        # Check if feedback exists in the question data
        if 'feedback' in current_question:
            st.write(f"**Feedback:** {current_question.get('feedback', '')}")
        
        # Navigation buttons
        col1, col2, col3, col4 = st.columns([1, 1, 1, 4])
        with col1:
            st.button("Previous", on_click=previous_question, disabled=st.session_state.current_question_index == 0)
        with col2:
            st.button("Next", on_click=next_question)
        with col3:
            st.button("Retry", on_click=lambda: setattr(st.session_state, "answered", False))

def create_donut_chart():
    """
    Create a donut chart showing the correct vs. incorrect answers
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor('none')  # Transparent background for the figure
    
    # Data
    correct_answers = st.session_state.correct_answers
    incorrect_answers = st.session_state.total_answered - correct_answers
    remaining_questions = len(st.session_state.questions) - st.session_state.total_answered
    
    # Data for the pie chart
    sizes = [correct_answers, incorrect_answers, remaining_questions]
    labels = ['Correct', 'Incorrect', 'Unanswered']
    colors = ['#4CAF50', '#F44336', '#9E9E9E']
    
    # Create a donut chart
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops={'width': 0.4, 'edgecolor': 'w'}
    )
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    plt.setp(autotexts, size=10, weight="bold", color="white")
    plt.setp(texts, size=12)
    
    # Title in the center
    ax.text(0, 0, f"{correct_answers}/{st.session_state.total_answered}", 
            ha='center', va='center', fontsize=20, fontweight='bold')
    
    # Add a subtitle
    ax.text(0, -0.12, 'Score', ha='center', va='center', fontsize=12)
    
    # Return the figure
    return fig

def get_chart_as_base64(fig):
    """
    Convert matplotlib figure to base64 string for embedding in HTML
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return img_str

def download_results():
    """
    Generate and download a summary of the quiz results
    """
    # Create donut chart
    fig = create_donut_chart()
    img_str = get_chart_as_base64(fig)
    
    # Data for the report
    correct_answers = st.session_state.correct_answers
    incorrect_answers = st.session_state.total_answered - correct_answers
    remaining_questions = len(st.session_state.questions) - st.session_state.total_answered
    success_rate = (correct_answers / st.session_state.total_answered * 100) if st.session_state.total_answered > 0 else 0
    
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
                <p>Generated on {st.session_state.get('date_completed', 'Not completed')}</p>
            </div>
            
            <h2>Performance Overview</h2>
            <div class="results">
                <div class="stat-box">
                    <div class="stat-value">{correct_answers}</div>
                    <div class="stat-label">Correct</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{incorrect_answers}</div>
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
            <p>You answered {st.session_state.total_answered} out of {len(st.session_state.questions)} total questions.</p>
            <p>Your success rate is {success_rate:.1f}% based on the {st.session_state.total_answered} questions you answered.</p>
            
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
    if 'date_completed' not in st.session_state:
        from datetime import datetime
        st.session_state.date_completed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Calculate the percentage based on answered questions only
    total_questions = len(st.session_state.questions)
    correct_answers = st.session_state.correct_answers
    total_answered = st.session_state.total_answered
    unanswered = total_questions - total_answered
    
    # Calculate percentage based on questions answered, not total questions
    percentage = (correct_answers / total_answered * 100) if total_answered > 0 else 0
    
    # Create layout with columns
    col1, col2 = st.columns([2, 2])
    
    with col1:
        st.header(f"Your Score: {correct_answers}/{total_answered} ({percentage:.1f}%)")
        
        # Progress bar for visual representation
        st.progress(percentage / 100)
        st.caption(f"Based on {total_answered} questions answered out of {total_questions} total questions")
        
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
            mime="text/html"
        )
    
    # Button to restart the quiz
    st.button("Start Over", on_click=reset_quiz)

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
    
    # Add a message about navigating questions
    st.markdown("""
    ### Instructions:
    - You can **skip** questions and return to them later.
    - Use the **Key Questions** button to see only the ordering questions.
    - Use the **Bookmarked** button to see questions you've bookmarked.
    - **Bookmark** important questions for later review.
    - Navigate with the **Previous** and **Next** buttons.
    - You can **retry** questions you have already answered.
    - After completing the quiz, you can **download your results**.
    """)
    

    
    # Check if the quiz is completed
    if st.session_state.quiz_completed:
        display_results()
    else:
        display_question()

if __name__ == "__main__":
    main()
