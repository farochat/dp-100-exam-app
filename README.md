# About this project
This repository is a fork on [JhonatanSmith/DP-100-Exam-Question-App](https://github.com/JhonatanSmith/DP-100-Exam-Question-App) made by [@JhonatanSmith](https://github.com/JhonatanSmith).

I started by editing questions, and decided to tackle down several updates to better emulate the exam setup and potentially to add more questions as well.

## Goal
This project aims to help people preparing for the [DP-100 certification](https://learn.microsoft.com/en-us/credentials/certifications/azure-data-scientist/?practice-assessment-type=certification). The goal is to have an app that emulates exam question that people can use in addition to the learning materials to practice for the certification exam.

# How to use it
1. Clone the repository
2. Set up the environment `uv` is strongly recommended but it can be done using `pip install -r requirements.txt` as well
3. Activate virtual environment
4. Run the app with `streamlit run app.py` (by default at `localhost:5000`)

# Questions format

The `questions.json` file is a json file that contains relevant informations related to practice questions, such as their type, the options, the correct answers and so on. These were hand-made, partially by the original author, partially by me.

Questions loading is currently hardcoded in the app. Questions can be added, removed, and modified by the user, provided it has the correct structure.

Questions are using the following format:
```(json)
{
      "question_id": <unique_identifier>,
      "type": <question_type> ,
      "question": <question_text>
      "options": [
          {
              "id": "A",
              "text": "Yes",
              "is_correct": false,
              "explanation": ""
          },
          {
              "id": "B",
              "text": "No",
              "is_correct": true,
              "explanation": ""
          }
      ],
      "feedback": "",
      "include_in_bank": true
}
```

To my knowledge there are no direct use for `question_id` which was initially intended to be used as an easy way to modify question but that is not currently functional, `include_in_bank` and it seems to be intended to filter upon loading them within the app, `explanation` is actively used only for certain question types.
## Supported types and comments
The supported types are initially `multiple_choice_single_answer`, `multiple_choice_multiple_answer`, `ordering`, `drag_and_drop_ordering`, `true_false`.

It seems that there are no difference between `ordering` and `drag_and_drop_ordering`, even if some `drag_and_drop_ordering` questions could technically be correct without correct order. `true_false` was modified to be a special case of `multiple_choice_single_answer` as that was the case in the original `questions.json`. But I believe it was intended to emulate the `yes/no` types of questions.

Currently the hotspot types (with dropdown list and fill in the blanks) are handled as special case of `multiple_choice_multiple_answers`.

# General explanation and issues
* There is a select theme features
* Exam mode/Practice mode: currently unclear, to be improved. Exam mode select a random set of 50 questions.
* Key questions: currently still there, I believe it was intended to be used for the questions that are scenarios and/or case studies, it is currently only used for the ordering.
* Bookmark questions


# Comment from the original author
> I hope this app will be usefull to help you pass the exam. If that is the case, please follow [My Personal LinkedIn account](https://www.linkedin.com/in/jhsgarciamu/) for more c: and i hope you use and pass the exam!! I wish you bests!
