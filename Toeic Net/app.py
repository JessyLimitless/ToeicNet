# 필요한 라이브러리 임포트
from flask import Flask, render_template, request, jsonify  # Flask 관련 기능을 가져옴
import openai  # OpenAI API 사용을 위한 라이브러리

# Flask 앱 생성
app = Flask(__name__)  # Flask 웹 애플리케이션 객체 생성

# OpenAI API 키 설정 (테스트용으로 하드코딩됨, 실제로는 환경 변수 사용 권장)
openai.api_key = "sk-"

# 첫 화면을 렌더링하는 함수 (홈 페이지)
@app.route('/')  # '/' 주소에 접근할 때 실행되는 함수
def index():
    return render_template('index.html')  # 'index.html' 파일을 사용자에게 보여줌

# 특정 TOEIC 문제를 생성하는 함수
def generate_question_for_part(part):
    # 각 TOEIC 파트에 대한 설명
    part_descriptions = {
        "Part 3": "Listen to a conversation between two or more people and answer questions about it.",  # Part 3 설명
        "Part 4": "Listen to a monologue (e.g., an announcement or speech) and answer questions."  # Part 4 설명
    }

    # 요청된 파트가 준비되지 않은 경우
    if part not in part_descriptions:
        return {
            'message': f"{part} is currently under preparation. Please check back later.",
            'question': None,  # 문제 없음
            'transcript': None,  # 대본 없음
            'correct_answer': None,  # 정답 없음
            'options': []  # 선택지 없음
        }

    # 요청된 파트에 대한 설명 가져오기
    description = part_descriptions.get(part, "TOEIC test question")  # 파트 설명 가져오기

    # OpenAI 모델에게 요청할 프롬프트(질문 요청 양식)
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

    # OpenAI API에 요청 보내기
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # OpenAI 모델 사용 (GPT-3.5)
            messages=[
                {"role": "system", "content": "You are an expert in TOEIC test preparation."},
                {"role": "user", "content": prompt}
            ]
        )

        # OpenAI의 응답을 가져옴
        content = response['choices'][0]['message']['content']

        # 응답이 필요한 필드를 포함하지 않을 경우 오류 발생
        if "Question:" not in content or "Correct Answer:" not in content:
            raise ValueError("The OpenAI response format is incorrect or missing sections.")

        # OpenAI 응답에서 각 부분 추출
        question = content.split("Question:")[1].split("Transcript:")[0].strip()  # 문제 부분
        transcript = content.split("Transcript:")[1].split("Correct Answer:")[0].strip()  # 대본 부분
        correct_answer = content.split("Correct Answer:")[1].split("Options:")[0].strip()  # 정답 부분
        options_text = content.split("Options:")[1].strip().split("\n")  # 선택지 부분
        options = [line.split(":")[1].strip() for line in options_text if ":" in line]  # A, B, C, D 선택지 추출

        # 반환할 데이터
        return {
            'question': question,
            'transcript': transcript,
            'correct_answer': correct_answer,
            'options': options
        }

    # 인증 실패 시 오류 처리
    except openai.error.AuthenticationError:
        return {'error': 'Invalid OpenAI API key. Please check your key.'}
    # 요청 제한 초과 시 오류 처리
    except openai.error.RateLimitError:
        return {'error': 'Rate limit exceeded. Please try again later.'}
    # 기타 예기치 않은 오류 처리
    except Exception as e:
        return {'error': f"Unexpected error occurred: {e}"}

# 사용자 요청에 따라 TOEIC 문제를 생성하는 API 엔드포인트
@app.route('/generate-question', methods=['GET'])  # 'GET' 요청 처리
def generate_question():
    part = request.args.get('part')  # URL 매개변수에서 'part' 값 가져오기
    if not part:
        return jsonify({'error': 'No TOEIC part specified'}), 400  # 'part'가 없을 경우 오류 반환

    question_data = generate_question_for_part(part)  # 요청된 파트에 대한 문제 생성
    return jsonify(question_data)  # JSON 형식으로 문제 반환

# 사용자가 제출한 답을 평가하는 API 엔드포인트
@app.route('/evaluate-answer', methods=['POST'])  # 'POST' 요청 처리
def evaluate_answer():
    data = request.json  # 요청 본문에서 JSON 데이터 가져오기
    user_answer = data.get('user_answer')  # 사용자 선택한 답안
    correct_answer = data.get('correct_answer')  # 정답

    # 필수 데이터가 누락된 경우 오류 반환
    if not user_answer or not correct_answer:
        return jsonify({'error': 'Missing user answer or correct answer'}), 400

    # 사용자에게 피드백 제공
    explanation = (
        f"You selected '{user_answer}', but the correct answer is '{correct_answer}'. "
        "The transcript indicates key information for understanding the correct answer. Make sure to listen for keywords."
    )

    return jsonify({'explanation': explanation})  # JSON 형식으로 설명 반환

# Flask 앱 실행
if __name__ == '__main__':
    app.run(debug=True)  # 디버그 모드로 실행 (개발 중 오류 메시지 표시)
