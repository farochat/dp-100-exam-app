import streamlit as st
import re
import pandas as pd
import random
import os

# Set page configuration
st.set_page_config(
    page_title="DP-100 Exam Simulator",
    page_icon="📚",
    layout="wide"
)

# Initialize session state for storing questions and navigation
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'show_explanation' not in st.session_state:
    st.session_state.show_explanation = False
if 'file_processed' not in st.session_state:
    st.session_state.file_processed = False
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0

def parse_markdown_content(content):
    """Parse the markdown content and extract questions"""
    questions = []
    
    # Split the content by question sections
    # Look specifically for headers starting with "## Pregunta" and "## ❓ Pregunta"
    question_pattern = r'(?:^|\n)(?:## Pregunta \d+|## ❓ Pregunta \d+)'
    question_blocks = re.split(question_pattern, content, flags=re.MULTILINE)
    
    # Skip the first block if it's just an introduction
    if question_blocks and not re.search(r'\*\*Pregunta:', question_blocks[0]):
        question_blocks = question_blocks[1:]
    
    # Process each block
    for i, block in enumerate(question_blocks):
        if block and len(block.strip()) > 10:  # Skip empty blocks
            question = parse_question_block(f"## Pregunta {i+1}{block}")
            if question and question.get('question_text'):
                questions.append(question)
    
    # Print diagnostic info
    print(f"Total questions extracted: {len(questions)}")
    return questions

def parse_question_block(block):
    """Parse a single question block and extract details"""
    if not block or len(block) < 10:  # Block too small
        return None
    
    question_data = {}
    
    # Extract question type
    type_match = re.search(r'\*\*Tipo:\*\*\s*(.*?)(?:\n|$)', block, re.IGNORECASE)
    if type_match:
        question_type = type_match.group(1).strip()
        # Translate to English
        if "única" in question_type.lower():
            question_data['type'] = "Single Choice"
        elif "múltiple" in question_type.lower():
            question_data['type'] = "Multiple Choice"
        elif "drag" in question_type.lower():
            question_data['type'] = "Drag and Drop"
        elif "drop" in question_type.lower():
            question_data['type'] = "Drop Down"
        elif "ordenar" in question_type.lower():
            question_data['type'] = "Ordering"
        else:
            question_data['type'] = question_type
    else:
        # Default to single choice
        question_data['type'] = "Single Choice"
    
    # Extract question text
    question_match = re.search(r'(?:## Pregunta \d+:?|## ❓ Pregunta \d+:?)\s*\n+(.*?)(?:\n+\*\*(?:Opciones|Tipo:|Respuesta)|---)', block, re.DOTALL)
    if not question_match:
        question_match = re.search(r'\*\*Pregunta:\*\*\s*\n+(.*?)(?:\n+\*\*(?:Opciones|Tipo:|Respuesta)|---)', block, re.DOTALL)
    
    if question_match:
        question_data['question_text'] = question_match.group(1).strip()
    else:
        # Try to extract from context
        context_match = re.search(r'\*\*Contexto\*\*:\s*(.*?)(?:\n+\*\*Pregunta\*\*:\s*(.*?))?(?:\n+\*\*Opciones\*\*:|$)', block, re.DOTALL)
        if context_match:
            context = context_match.group(1).strip()
            question = context_match.group(2).strip() if context_match.group(2) else ""
            question_data['question_text'] = f"{context}\n\n{question}"
        else:
            # Try a more generic extraction
            solution_match = re.search(r'\*\*Solution:\*\*\s*(.*?)(?:\n+\*\*|---|\n\n)', block, re.DOTALL)
            if solution_match:
                question_data['question_text'] = solution_match.group(1).strip()
            else:
                # If no other pattern matches, use a simple extraction
                first_lines = block.split('\n')[:5]
                question_data['question_text'] = '\n'.join([line for line in first_lines if not line.startswith('#') and not '**Tipo' in line])
    
    # Extract options
    options = []
    options_match = re.findall(r'- \[([ xX✓✅])\] (.*?)(?:\n|$)', block)
    if options_match:
        for checked, option_text in options_match:
            is_correct = checked.strip() in ['x', 'X', '✓', '✅'] 
            options.append({
                'text': option_text.strip(),
                'is_correct': is_correct
            })
        question_data['options'] = options
        
        # Determine if it's multiple choice
        if sum(1 for opt in options if opt['is_correct']) > 1:
            question_data['type'] = "Multiple Choice"
    
    # Extract correct answer
    correct_answer_match = re.search(r'\*\*Respuesta Correcta:\*\*\s*(.*?)(?:\n|$)', block)
    if correct_answer_match:
        question_data['correct_answer'] = correct_answer_match.group(1).strip()
    
    # Extract explanation
    explanation_match = re.search(r'\*\*Explicación:\*\*\s*(.*?)(?:\n+\*\*|---|\n\n\n|$)', block, re.DOTALL)
    if explanation_match:
        question_data['explanation'] = explanation_match.group(1).strip()
    
    # Extract reference
    reference_match = re.search(r'(?:\*\*Referencia(?:\s+oficial)?:\*\*|\📚(?:\s+\*\*)?Referencia(?:\s+oficial)?(?:\*\*)?:)\s*(.*?)(?:\n+\*\*|---|\n\n\n|$)', block, re.DOTALL)
    if reference_match:
        question_data['reference'] = reference_match.group(1).strip()
    
    return question_data

def navigate_to_next():
    """Navigate to the next question"""
    if st.session_state.current_index < len(st.session_state.questions) - 1:
        st.session_state.current_index += 1
        st.session_state.show_explanation = False
    
def navigate_to_prev():
    """Navigate to the previous question"""
    if st.session_state.current_index > 0:
        st.session_state.current_index -= 1
        st.session_state.show_explanation = False

def navigate_to_random():
    """Navigate to a random question"""
    if len(st.session_state.questions) > 0:
        st.session_state.current_index = random.randint(0, len(st.session_state.questions) - 1)
        st.session_state.show_explanation = False

def check_answer():
    """Check if the answer is correct and show explanation"""
    st.session_state.show_explanation = True

def reset_question():
    """Reset the current question answer"""
    question_idx = str(st.session_state.current_index)
    if question_idx in st.session_state.user_answers:
        del st.session_state.user_answers[question_idx]
    st.session_state.show_explanation = False

def process_file(file_content):
    """Process the file content and extract questions"""
    questions = parse_markdown_content(file_content)
    if questions:
        st.session_state.questions = questions
        st.session_state.total_questions = len(questions)
        st.session_state.current_index = random.randint(0, len(questions) - 1)
        st.session_state.file_processed = True
        return True
    return False

# Load the markdown file
if not st.session_state.file_processed:
    file_path = os.path.join('attached_assets', 'preguntasChatGPT.md')
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
            if process_file(file_content):
                st.session_state.file_processed = True
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")

# Main application
st.title("DP-100 Exam Simulator")
st.write("This simulator helps you prepare for the Microsoft Azure Data Scientist Associate DP-100 exam.")

# Display the current question
if st.session_state.file_processed and st.session_state.questions:
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("⬅️ Previous Question", disabled=st.session_state.current_index == 0):
            navigate_to_prev()
    
    with col2:
        st.write(f"**Question {st.session_state.current_index + 1} of {len(st.session_state.questions)}**")
    
    with col3:
        if st.button("Next Question ➡️", disabled=st.session_state.current_index == len(st.session_state.questions) - 1):
            navigate_to_next()
    
    # Get current question
    current_question = st.session_state.questions[st.session_state.current_index]
    
    # Display question type
    if 'type' in current_question:
        st.write(f"**Type:** {current_question['type']}")
    
    # Display question
    st.markdown("### Question")
    st.markdown(current_question['question_text'])
    
    # Display options and handle user input based on question type
    question_idx = str(st.session_state.current_index)
    
    if 'options' in current_question:
        st.markdown("### Options")
        
        if "Multiple" in current_question['type']:
            # Multiple selection question
            options = [opt['text'] for opt in current_question['options']]
            
            selected_options = st.multiselect(
                "Select one or more options:",
                options,
                key=f"multiselect_{st.session_state.current_index}"
            )
            
            if selected_options:
                st.session_state.user_answers[question_idx] = selected_options
        
        elif "Drag" in current_question['type']:
            # Drag and drop question (simulated with selectbox)
            st.info("This is a Drag and Drop question. Due to technical limitations, it's simulated with selectboxes.")
            
            options = [opt['text'] for opt in current_question['options']]
            targets = [f"Target {i+1}" for i in range(len(options))]
            
            for i, target in enumerate(targets):
                selected = st.selectbox(
                    f"Drag an option to {target}:",
                    [""] + options,
                    key=f"dragdrop_{st.session_state.current_index}_{i}"
                )
                
                if selected:
                    if question_idx not in st.session_state.user_answers:
                        st.session_state.user_answers[question_idx] = {}
                    st.session_state.user_answers[question_idx][target] = selected
        
        elif "Drop" in current_question['type']:
            # Drop down question
            options = [opt['text'] for opt in current_question['options']]
            
            selected_option = st.selectbox(
                "Select an option:",
                [""] + options,
                key=f"dropdown_{st.session_state.current_index}"
            )
            
            if selected_option:
                st.session_state.user_answers[question_idx] = selected_option
        
        elif "Ordering" in current_question['type']:
            # Ordering question (simulated with numbered selectboxes)
            st.info("This question requires ordering options. Due to technical limitations, it's simulated with numbered selectboxes.")
            
            options = [opt['text'] for opt in current_question['options']]
            
            for i in range(len(options)):
                selected = st.selectbox(
                    f"Position {i+1}:",
                    [""] + options,
                    key=f"order_{st.session_state.current_index}_{i}"
                )
                
                if selected:
                    if question_idx not in st.session_state.user_answers:
                        st.session_state.user_answers[question_idx] = {}
                    st.session_state.user_answers[question_idx][f"Pos {i+1}"] = selected
        
        else:
            # Single selection question (default)
            options = [opt['text'] for opt in current_question['options']]
            selected_option = st.radio(
                "Select an option:",
                options,
                index=None,
                key=f"radio_{st.session_state.current_index}"
            )
            
            if selected_option:
                st.session_state.user_answers[question_idx] = selected_option
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset Answer"):
            reset_question()
    
    with col2:
        if st.button("✅ Check Answer"):
            check_answer()
    
    with col3:
        if st.button("🎲 Random Question"):
            navigate_to_random()
    
    # Show explanation if requested
    if st.session_state.show_explanation:
        st.markdown("---")
        st.markdown("### Correct Answer")
        
        # Display correct options
        if 'options' in current_question:
            correct_options = [opt['text'] for opt in current_question['options'] if opt['is_correct']]
            if correct_options:
                if len(correct_options) > 1:
                    st.success("The correct answers are:")
                    for opt in correct_options:
                        st.write(f"- {opt}")
                else:
                    st.success(f"The correct answer is: {correct_options[0]}")
        elif 'correct_answer' in current_question:
            st.success(f"The correct answer is: {current_question['correct_answer']}")
        
        # Display explanation if available
        if 'explanation' in current_question and current_question['explanation']:
            st.markdown("### Explanation")
            st.markdown(current_question['explanation'])
        
        # Display reference if available
        if 'reference' in current_question and current_question['reference']:
            st.markdown("### Reference")
            st.markdown(current_question['reference'])
else:
    st.warning("Waiting for questions to load...")

# Add footer 
st.markdown("---")
st.write(f"© 2023 DP-100 Exam Simulator | {st.session_state.total_questions} questions available")