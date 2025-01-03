from flask import Flask, render_template, request, jsonify
import openai

app = Flask(__name__)

# OpenAI API Key (hardcoded for testing)
openai.api_key = "sk-"

# Render the home page
@app.route('/')
def index():
    return render_template('index.html')

# Generate a TOEIC question
def generate_question_for_part(part):
    part_descriptions = {
        "Part 3": "Listen to a conversation between two or more people and answer questions about it.",
        "Part 4": "Listen to a monologue (e.g., an announcement or speech) and answer questions."
    }

    if part not in part_descriptions:
        return {
            'message': f"{part} is currently under preparation. Please check back later.",
            'question': None,
            'transcript': None,
            'correct_answer': None,
            'options': []
        }

    description = part_descriptions.get(part, "TOEIC test question")
    prompt = f"""
    Generate a TOEIC {part} question. Description: {description}.
    Please include:
    1. A detailed **question** text relevant to the part.
    2. A **transcript** of the conversation, short talk, or passage (if applicable).
    3. The correct answer and corresponding options (A, B, C, D).
    Response format:
    Question: [Your question text]
    Transcript: [The transcript of what is heard]
    Correct Answer: [A, B, C, or D]
    Options:
    - A: [Option A text]
    - B: [Option B text]
    - C: [Option C text]
    - D: [Option D text]
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in TOEIC test preparation."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response['choices'][0]['message']['content']

        if "Question:" not in content or "Correct Answer:" not in content:
            raise ValueError("The OpenAI response format is incorrect or missing sections.")

        question = content.split("Question:")[1].split("Transcript:")[0].strip()
        transcript = content.split("Transcript:")[1].split("Correct Answer:")[0].strip()
        correct_answer = content.split("Correct Answer:")[1].split("Options:")[0].strip()
        options_text = content.split("Options:")[1].strip().split("\n")
        options = [line.split(":")[1].strip() for line in options_text if ":" in line]

        return {
            'question': question,
            'transcript': transcript,
            'correct_answer': correct_answer,
            'options': options
        }

    except openai.error.AuthenticationError:
        return {'error': 'Invalid OpenAI API key. Please check your key.'}
    except openai.error.RateLimitError:
        return {'error': 'Rate limit exceeded. Please try again later.'}
    except Exception as e:
        return {'error': f"Unexpected error occurred: {e}"}

@app.route('/generate-question', methods=['GET'])
def generate_question():
    part = request.args.get('part')
    if not part:
        return jsonify({'error': 'No TOEIC part specified'}), 400

    question_data = generate_question_for_part(part)
    return jsonify(question_data)

@app.route('/evaluate-answer', methods=['POST'])
def evaluate_answer():
    data = request.json
    user_answer = data.get('user_answer')
    correct_answer = data.get('correct_answer')

    if not user_answer or not correct_answer:
        return jsonify({'error': 'Missing user answer or correct answer'}), 400

    explanation = (
        f"You selected '{user_answer}', but the correct answer is '{correct_answer}'. "
        "The transcript indicates key information for understanding the correct answer. Make sure to listen for keywords."
    )

    return jsonify({'explanation': explanation})

if __name__ == '__main__':
    app.run(debug=True)
