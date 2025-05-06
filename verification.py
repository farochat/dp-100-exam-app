import json

file_path = "./questions.json"

try:
    with open(file_path, "r", encoding="utf-8") as file:
        questions = json.load(file)

    # Total number of questions
    print(f"Total de preguntas cargadas: {len(questions)}\n")

except json.JSONDecodeError as e:
    print("Error de formato en el archivo JSON:")
    print(e)

except Exception as e:
    print("Otro error al leer el JSON:")
    print(e)
