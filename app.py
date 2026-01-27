from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import hashlib
import secrets
import base64
import json
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import PyPDF2
import io
from werkzeug.utils import secure_filename
import re

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-it-in-production')
CORS(app, supports_credentials=True, origins=['http://127.0.0.1:5001'])

DATABASE = 'octocode.db'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PDF Upload Configuration
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Get API key from environment variable
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env file!")

groq_client = Groq(api_key=GROQ_API_KEY)


def hash_password(password):
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"


def verify_password(password, hashed):
    try:
        salt, pwd_hash = hashed.split('$')
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except Exception:
        return False


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def safe_dict(row):
    """Безопасное преобразование Row в dict"""
    if row is None:
        return None
    d = dict(row)
    if 'points' in d:
        d['points'] = d['points'] if d['points'] is not None else 0
    if 'points_reward' in d:
        d['points_reward'] = d['points_reward'] if d['points_reward'] is not None else 1000
    return d


def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"

        # Clean up text
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"❌ PDF extraction error: {e}")
        return None


def init_db():
    print("Initialising the database...")
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       password
                       TEXT
                       NOT
                       NULL,
                       role
                       TEXT
                       DEFAULT
                       'student',
                       points
                       INTEGER
                       DEFAULT
                       0,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    # 2. Profiles
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS profiles
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       UNIQUE
                       NOT
                       NULL,
                       avatar_url
                       TEXT,
                       birthdate
                       DATE,
                       country
                       TEXT,
                       bio
                       TEXT,
                       favorite_language
                       TEXT,
                       experience_level
                       TEXT
                       DEFAULT
                       'beginner',
                       profile_visible
                       BOOLEAN
                       DEFAULT
                       1,
                       friend_requests
                       BOOLEAN
                       DEFAULT
                       1,
                       email_notifications
                       BOOLEAN
                       DEFAULT
                       1,
                       updated_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 3. Courses
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS courses
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       category
                       TEXT,
                       color
                       TEXT,
                       total_lessons
                       INTEGER
                       DEFAULT
                       0,
                       duration
                       TEXT,
                       rating
                       REAL
                       DEFAULT
                       0,
                       status
                       TEXT
                       DEFAULT
                       'active'
                   )
                   ''')

    # 4. Enrollments
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS enrollments
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       course_id
                       INTEGER
                       NOT
                       NULL,
                       enrolled_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       UNIQUE
                   (
                       user_id,
                       course_id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE,
                       FOREIGN KEY
                   (
                       course_id
                   ) REFERENCES courses
                   (
                       id
                   )
                     ON DELETE CASCADE
                       )
                   ''')

    # 5. AI Tasks
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS ai_tasks
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       task_id
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       topic
                       TEXT,
                       difficulty
                       TEXT,
                       language
                       TEXT,
                       examples
                       TEXT,
                       hints
                       TEXT,
                       solution
                       TEXT,
                       test_cases
                       TEXT,
                       estimated_time
                       INTEGER,
                       points_reward
                       INTEGER
                       DEFAULT
                       1000,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       completed
                       BOOLEAN
                       DEFAULT
                       0,
                       completed_at
                       TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 6. AI Submissions
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS ai_submissions
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       task_id
                       TEXT
                       NOT
                       NULL,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       code
                       TEXT
                       NOT
                       NULL,
                       passed_tests
                       INTEGER
                       DEFAULT
                       0,
                       total_tests
                       INTEGER
                       DEFAULT
                       0,
                       points_earned
                       INTEGER
                       DEFAULT
                       0,
                       submitted_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 7. Friendships
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS friendships
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       friend_id
                       INTEGER
                       NOT
                       NULL,
                       status
                       TEXT
                       DEFAULT
                       'pending',
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       UNIQUE
                   (
                       user_id,
                       friend_id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE,
                       FOREIGN KEY
                   (
                       friend_id
                   ) REFERENCES users
                   (
                       id
                   )
                     ON DELETE CASCADE
                       )
                   ''')

    # 8. Points History
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS points_history
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       points
                       INTEGER
                       NOT
                       NULL,
                       reason
                       TEXT,
                       task_id
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 9. Quizzes table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS quizzes
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       course_id
                       INTEGER
                       NOT
                       NULL,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       questions_json
                       TEXT
                       NOT
                       NULL,
                       attempt_number
                       INTEGER
                       DEFAULT
                       1,
                       created_at
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       course_id
                   ) REFERENCES courses
                   (
                       id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # 10. Quiz answers table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS quiz_answers
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       quiz_id
                       INTEGER
                       NOT
                       NULL,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       answers_json
                       TEXT
                       NOT
                       NULL,
                       score
                       INTEGER
                       NOT
                       NULL,
                       passed
                       INTEGER
                       NOT
                       NULL,
                       feedback
                       TEXT,
                       submitted_at
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       quiz_id
                   ) REFERENCES quizzes
                   (
                       id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # 11. Quiz PDFs table (NEW)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS quiz_pdfs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       quiz_id
                       INTEGER
                       NOT
                       NULL,
                       filename
                       TEXT
                       NOT
                       NULL,
                       pdf_text
                       TEXT,
                       uploaded_by
                       INTEGER
                       NOT
                       NULL,
                       uploaded_at
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       quiz_id
                   ) REFERENCES quizzes
                   (
                       id
                   ) ON DELETE CASCADE,
                       FOREIGN KEY
                   (
                       uploaded_by
                   ) REFERENCES users
                   (
                       id
                   )
                     ON DELETE CASCADE
                       )
                   ''')

    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "teacher"')
    teacher_count = cursor.fetchone()['count']

    if teacher_count == 0:
        print("👨‍🏫 Создаем тестового учителя...")
        hashed = hash_password('teacher123')
        cursor.execute('INSERT INTO users (name, email, password, role, points) VALUES (?, ?, ?, ?, ?)',
                       ('Herr Schmidt', 'teacher@octocode.de', hashed, 'teacher', 0))
        teacher_id = cursor.lastrowid
        cursor.execute('INSERT INTO profiles (user_id) VALUES (?)', (teacher_id,))
        print("✅ Тестовый учитель создан: teacher@octocode.de / teacher123")

    cursor.execute('SELECT COUNT(*) as count FROM courses')
    course_count = cursor.fetchone()['count']

    if course_count == 0:
        print("📚 Сreating Courses ...")
        test_courses = [
            ('Python Grundlagen', 'Lerne die Basics von Python', 'Programmierung', '#3b82f6', 12, '8 Wochen', 4.5,
             'active'),
            ('JavaScript für Anfänger', 'Webentwicklung mit JS', 'Web Development', '#f59e0b', 10, '6 Wochen', 4.3,
             'active'),
            ('HTML & CSS Basics', 'Erstelle deine erste Website', 'Web Design', '#10b981', 8, '4 Wochen', 4.7,
             'active'),
        ]
        for course in test_courses:
            cursor.execute('''
                           INSERT INTO courses (title, description, category, color, total_lessons, duration, rating,
                                                status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           ''', course)
        print(f" {len(test_courses)} Kurse erstellt")

    db.commit()
    db.close()
    print("Database initialised")


class TaskGenerator:
    def __init__(self):
        self.client = groq_client

    def generate_task(self, topic: str, user_id: int, difficulty: str = "Mittel", language: str = "Python"):
        seed = hashlib.md5(f"{user_id}_{topic}_{secrets.token_hex(8)}".encode()).hexdigest()[:8]

        points_map = {"Einfach": 500, "Mittel": 1000, "Schwer": 2000}
        points_reward = points_map.get(difficulty, 1000)

        prompt = f"""Du bist ein erfahrener Programmierlehrer. Erstelle eine einzigartige Programmieraufgabe auf Deutsch.

Parameter:
- Thema: {topic}
- Programmiersprache: {language}
- Schwierigkeitsgrad: {difficulty}

Erstelle eine praktische Aufgabe für Kinder/Jugendliche.

Antworte NUR mit JSON:
{{
  "title": "Kurzer Titel der Aufgabe",
  "description": "Detaillierte Beschreibung (2-3 Sätze)",
  "difficulty": "{difficulty}",
  "topic": "{topic}",
  "examples": [
    {{"input": "Beispiel 1", "output": "Ausgabe 1", "explanation": "Erklärung"}},
    {{"input": "Beispiel 2", "output": "Ausgabe 2", "explanation": "Erklärung"}}
  ],
  "hints": ["Tipp 1", "Tipp 2", "Tipp 3"],
  "solution": "# Musterlösung\\ncode hier",
  "test_cases": [
    {{"input": "Test 1", "expected_output": "Ausgabe 1"}},
    {{"input": "Test 2", "expected_output": "Ausgabe 2"}}
  ],
  "estimated_time": 30
}}

NUR JSON, ohne Code-Blöcke!"""

        try:
            print(f"🤖 Generiere Task für User {user_id}, Thema: {topic}, Schwierigkeit: {difficulty}")

            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Du bist ein Programmierlehrer. Antworte NUR mit gültigem JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=1
            )

            text = completion.choices[0].message.content.strip()
            text = text.replace("```json", "").replace("```", "").strip()

            task_data = json.loads(text)
            task_data["task_id"] = seed
            task_data["language"] = language
            task_data["points_reward"] = points_reward

            print(f"✅ Task generiert: {task_data['title']}")
            return task_data

        except Exception as e:
            print(f"❌ AI Error: {e}")
            import traceback
            traceback.print_exc()
            return None


class PDFQuizGenerator:
    def __init__(self):
        self.client = groq_client

    def generate_quiz_from_pdf(self, pdf_text: str, num_questions: int = 10, difficulty: str = "medium"):
        """Generate quiz questions from PDF content using AI"""

        # Truncate text if too long (keep first 4000 chars for context)
        if len(pdf_text) > 4000:
            pdf_text = pdf_text[:4000] + "..."

        difficulty_map = {
            "easy": "einfach - Grundlegende Konzepte aus dem Dokument",
            "medium": "mittel - Anwendung und Verständnis der Konzepte",
            "hard": "schwer - Tiefes Verständnis und kritisches Denken"
        }

        difficulty_desc = difficulty_map.get(difficulty, difficulty_map["medium"])

        # Calculate code vs multiple choice split
        num_code = int(num_questions * 0.3)  # 30% code/practical
        num_multiple = num_questions - num_code  # 70% multiple choice

        prompt = f"""Du bist ein Experte für Bildungsinhalte. Erstelle ein Quiz mit GENAU {num_questions} Fragen basierend AUSSCHLIESSLICH auf dem folgenden Dokument.

DOKUMENT-INHALT:
{pdf_text}

Schwierigkeitsgrad: {difficulty_desc}

WICHTIG - FRAGEN-ANFORDERUNGEN:
- Erstelle GENAU {num_questions} Fragen
- Davon {num_multiple} Multiple-Choice Fragen
- Davon {num_code} praktische/Code-Fragen (falls relevant)
- ALLE Fragen müssen DIREKT aus dem Dokument stammen
- Keine allgemeinen Wissensfragen, die nicht im Dokument stehen
- Jede Frage MUSS mit Informationen aus dem Dokument beantwortbar sein

Erstelle ein JSON-Objekt mit folgendem Format:
{{
    "questions": [
        {{
            "id": 1,
            "type": "multiple_choice",
            "difficulty": "{difficulty}",
            "question": "Frage basierend auf dem Dokument?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Erklärung mit Bezug zum Dokument"
        }},
        {{
            "id": 2,
            "type": "code",
            "difficulty": "{difficulty}",
            "question": "Praktische Aufgabe aus dem Dokument",
            "code": "# Code-Beispiel falls relevant",
            "options": ["Lösung A", "Lösung B", "Lösung C", "Lösung D"],
            "correct_answer": 0,
            "explanation": "Erklärung basierend auf Dokument-Inhalt"
        }}
    ]
}}

NUR JSON zurückgeben, KEINE zusätzlichen Texte, KEINE Markdown-Formatierung."""

        try:
            print(f"🤖 Generating quiz from PDF content...")

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein professioneller Quiz-Generator. Erstelle Fragen AUSSCHLIESSLICH basierend auf dem bereitgestellten Dokument. Antworte NUR mit validem JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=4000,
                top_p=0.9
            )

            response_text = response.choices[0].message.content.strip()

            # Clean response
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            quiz_data = json.loads(response_text)

            # Validate and ensure correct number of questions
            actual_count = len(quiz_data.get('questions', []))
            print(f"✅ Generated {actual_count} questions from PDF")

            # Add unique IDs
            for i, question in enumerate(quiz_data['questions']):
                question['id'] = i + 1
                if 'difficulty' not in question:
                    question['difficulty'] = difficulty
                if 'type' not in question:
                    question['type'] = 'multiple_choice'

            return quiz_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return self._get_fallback_quiz(num_questions, difficulty)
        except Exception as e:
            print(f"❌ Quiz generation error: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_quiz(num_questions, difficulty)

    def _get_fallback_quiz(self, num_questions=10, difficulty="medium"):
        """Fallback quiz if AI generation fails"""
        print(f"⚠️ Using fallback quiz with {num_questions} questions")

        questions = []
        for i in range(num_questions):
            questions.append({
                "id": i + 1,
                "type": "multiple_choice",
                "difficulty": difficulty,
                "question": f"Fallback Frage {i + 1}: Bitte laden Sie das Dokument erneut hoch.",
                "options": [
                    "Option A",
                    "Option B",
                    "Option C",
                    "Option D"
                ],
                "correct_answer": 0,
                "explanation": "Dies ist eine Fallback-Frage. Bitte generieren Sie das Quiz erneut."
            })

        return {"questions": questions}


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = (data.get('password') or '').strip()
        role = data.get('role', 'student')

        if not name or not email or not password:
            return jsonify({'success': False, 'message': 'Alle Felder sind erforderlich!'}), 400
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Passwort muss mindestens 6 Zeichen haben!'}), 400

        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            db.close()
            return jsonify({'success': False, 'message': 'E-Mail bereits registriert!'}), 400

        hashed = hash_password(password)
        cursor = db.execute('INSERT INTO users (name, email, password, role, points) VALUES (?, ?, ?, ?, ?)',
                            (name, email, hashed, role, 0))
        user_id = cursor.lastrowid
        db.execute('INSERT INTO profiles (user_id) VALUES (?)', (user_id,))
        db.commit()
        db.close()

        print(f"✅ Neuer Benutzer registriert: {name} ({email})")
        return jsonify({'success': True, 'message': 'Registrierung erfolgreich!'}), 201

    except Exception as e:
        print(f"❌ Registrierungsfehler: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = (data.get('password') or '').strip()

        if not email or not password:
            return jsonify({'success': False, 'message': 'E-Mail und Passwort erforderlich!'}), 400

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND role = ?', (email, 'student')).fetchone()
        db.close()

        if not user:
            return jsonify({'success': False, 'message': 'Falsche E-Mail oder Passwort!'}), 401

        if not verify_password(password, user['password']):
            return jsonify({'success': False, 'message': 'Falsche E-Mail oder Passwort!'}), 401

        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = user['role']

        user_dict = safe_dict(user)
        print(f"✅ Login erfolgreich: {user_dict['name']} (Points: {user_dict['points']})")

        return jsonify({
            'success': True,
            'message': f'Willkommen, {user_dict["name"]}!',
            'user': {
                'id': user_dict['id'],
                'name': user_dict['name'],
                'email': user_dict['email'],
                'role': user_dict['role'],
                'points': user_dict['points']
            },
            'redirect': '/dashboard.html'
        }), 200

    except Exception as e:
        print(f"❌ Login-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500


@app.route('/api/teacher-login', methods=['POST'])
def teacher_login():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        password = (data.get('password') or '').strip()

        if not email or not password:
            return jsonify({'success': False, 'message': 'E-Mail und Passwort erforderlich!'}), 400

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND role = ?', (email, 'teacher')).fetchone()
        db.close()

        if not user or not verify_password(password, user['password']):
            return jsonify({'success': False, 'message': 'Falsche E-Mail oder Passwort!'}), 401

        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['user_role'] = 'teacher'

        print(f"✅ Lehrer Login: {user['name']}")

        return jsonify({
            'success': True,
            'message': f'Willkommen, {user["name"]}!',
            'redirect': '/teacher-dashboard.html'
        }), 200

    except Exception as e:
        print(f"❌ Teacher login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Abgemeldet!'}), 200


@app.route('/api/check-auth')
def check_auth():
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 200

    try:
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

        if not user:
            db.close()
            return jsonify({'authenticated': False}), 200

        profile = db.execute('SELECT avatar_url FROM profiles WHERE user_id = ?', (session['user_id'],)).fetchone()
        db.close()

        user_dict = safe_dict(user)

        avatar_url = profile['avatar_url'] if profile and profile['avatar_url'] else \
            f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_dict['name']}"

        return jsonify({
            'authenticated': True,
            'user': {
                'id': user_dict['id'],
                'name': user_dict['name'],
                'email': user_dict['email'],
                'role': user_dict['role'],
                'avatar_url': avatar_url,
                'points': user_dict['points']
            }
        }), 200

    except Exception as e:
        print(f"❌ Auth check error: {e}")
        return jsonify({'authenticated': False}), 200


# ============ TEACHER API ENDPOINTS ============
@app.route('/api/teacher/students', methods=['GET'])
def get_teacher_students():
    """Получить всех студентов для учителя"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Не авторизован'}), 401

    try:
        db = get_db()

        students = db.execute('''
                              SELECT u.id,
                                     u.name,
                                     u.email,
                                     u.points,
                                     u.created_at,
                                     p.avatar_url,
                                     p.experience_level,
                                     COUNT(DISTINCT e.course_id)                               as coursesCompleted,
                                     COUNT(DISTINCT at.id)                                     as totalTasks,
                                     COUNT(DISTINCT CASE WHEN at.completed = 1 THEN at.id END) as completedTasks
                              FROM users u
                                       LEFT JOIN profiles p ON u.id = p.user_id
                                       LEFT JOIN enrollments e ON u.id = e.user_id
                                       LEFT JOIN ai_tasks at
                              ON u.id = at.user_id
                              WHERE u.role = 'student'
                              GROUP BY u.id
                              ORDER BY u.points DESC
                              ''').fetchall()

        db.close()

        students_list = []
        for student in students:
            student_dict = safe_dict(student)
            # Вычисляем прогресс
            total_tasks = student_dict.get('totalTasks', 0)
            completed_tasks = student_dict.get('completedTasks', 0)
            progress = round((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

            student_dict['progress'] = progress
            student_dict['activeCourses'] = student_dict.get('coursesCompleted', 0)

            if not student_dict.get('avatar_url'):
                student_dict['avatar_url'] = f"https://api.dicebear.com/7.x/avataaars/svg?seed={student_dict['name']}"

            students_list.append(student_dict)

        print(f"✅ Загружено {len(students_list)} студентов для учителя")
        return jsonify(students_list), 200

    except Exception as e:
        print(f"❌ Get students error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500


@app.route('/api/teacher/tasks', methods=['GET'])
def get_teacher_tasks():
    """Получить все задачи для учителя"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Не авторизован'}), 401

    try:
        db = get_db()

        tasks = db.execute('''
                           SELECT at.id,
                                  at.task_id,
                                  at.title,
                                  at.description,
                                  at.topic,
                                  at.difficulty,
                                  at.language,
                                  at.estimated_time,
                                  at.points_reward,
                                  at.created_at,
                                  COUNT(DISTINCT ats.user_id)                                    as submissions,
                                  COUNT(DISTINCT CASE WHEN at.completed = 1 THEN at.user_id END) as completed
                           FROM ai_tasks at
			LEFT JOIN ai_submissions ats
                           ON at.task_id = ats.task_id
                           GROUP BY at.task_id
                           ORDER BY at.created_at DESC
                           ''').fetchall()

        db.close()

        tasks_list = [safe_dict(task) for task in tasks]

        print(f"✅ Загружено {len(tasks_list)} задач для учителя")
        return jsonify(tasks_list), 200

    except Exception as e:
        print(f"❌ Get teacher tasks error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500


@app.route('/api/teacher/stats', methods=['GET'])
def get_teacher_stats():
    """Получить статистику для учителя"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Не авторизован'}), 401

    try:
        db = get_db()

        # Количество студентов
        students_count = db.execute('SELECT COUNT(*) as count FROM users WHERE role = "student"').fetchone()['count']

        # Количество курсов
        courses_count = db.execute('SELECT COUNT(*) as count FROM courses').fetchone()['count']

        # Количество задач
        tasks_count = db.execute('SELECT COUNT(*) as count FROM ai_tasks').fetchone()['count']

        # Средний прогресс
        avg_progress = db.execute('''
                                  SELECT AVG(
                                                 CASE
                                                     WHEN total_tasks > 0 THEN (completed_tasks * 100.0 / total_tasks)
                                                     ELSE 0
                                                     END
                                         ) as avg_progress
                                  FROM (SELECT u.id,
                                               COUNT(DISTINCT at.id)                                     as total_tasks,
                                               COUNT(DISTINCT CASE WHEN at.completed = 1 THEN at.id END) as completed_tasks
                                        FROM users u
                                                 LEFT JOIN ai_tasks at
                                        ON u.id = at.user_id
                                        WHERE u.role = 'student'
                                        GROUP BY u.id)
                                  ''').fetchone()

        db.close()

        stats = {
            'totalStudents': students_count,
            'totalCourses': courses_count,
            'totalTasks': tasks_count,
            'avgProgress': round(avg_progress['avg_progress'] or 0)
        }

        print(f"✅ Статистика загружена: {stats}")
        return jsonify(stats), 200

    except Exception as e:
        print(f"❌ Get stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'totalStudents': 0,
            'totalCourses': 0,
            'totalTasks': 0,
            'avgProgress': 0
        }), 500


# ============ AI TASKS ============

@app.route('/api/ai/generate-task', methods=['POST'])
def ai_generate_task():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

    try:
        data = request.get_json() or {}
        topic = data.get('topic', 'Python Grundlagen')
        difficulty = data.get('difficulty', 'Mittel')
        language = data.get('language', 'Python')

        print(f"📝 Generiere Aufgabe: {topic}, {difficulty}, {language}")

        generator = TaskGenerator()
        task_data = generator.generate_task(topic, session['user_id'], difficulty, language)

        if not task_data:
            return jsonify({'success': False, 'message': 'AI-Generierung fehlgeschlagen'}), 500

        db = get_db()
        db.execute('''
                   INSERT INTO ai_tasks (user_id, task_id, title, description, topic, difficulty, language,
                                         examples, hints, solution, test_cases, estimated_time, points_reward)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ''', (
                       session['user_id'],
                       task_data['task_id'],
                       task_data['title'],
                       task_data['description'],
                       task_data['topic'],
                       task_data['difficulty'],
                       task_data['language'],
                       json.dumps(task_data['examples'], ensure_ascii=False),
                       json.dumps(task_data['hints'], ensure_ascii=False),
                       task_data['solution'],
                       json.dumps(task_data['test_cases'], ensure_ascii=False),
                       task_data.get('estimated_time', 30),
                       task_data.get('points_reward', 1000)
                   ))
        db.commit()
        db.close()

        print(f"✅ Aufgabe gespeichert: {task_data['title']}")
        return jsonify({'success': True, 'task': task_data}), 200

    except Exception as e:
        print(f"❌ Generate task error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500


@app.route('/api/ai/my-tasks', methods=['GET'])
def ai_get_my_tasks():
    if 'user_id' not in session:
        return jsonify([]), 200

    try:
        db = get_db()
        tasks = db.execute('''
                           SELECT id,
                                  task_id,
                                  title,
                                  description,
                                  topic,
                                  difficulty, language, estimated_time, points_reward, created_at, completed
                           FROM ai_tasks
                           WHERE user_id = ?
                           ORDER BY created_at DESC
                           ''', (session['user_id'],)).fetchall()
        db.close()

        return jsonify([safe_dict(t) for t in tasks]), 200

    except Exception as e:
        print(f"❌ Get tasks error: {e}")
        return jsonify([]), 200


@app.route('/api/ai/task/<task_id>', methods=['GET'])
def ai_get_task(task_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

    try:
        db = get_db()
        task = db.execute('SELECT * FROM ai_tasks WHERE task_id = ? AND user_id = ?',
                          (task_id, session['user_id'])).fetchone()
        db.close()

        if not task:
            return jsonify({'success': False, 'message': 'Aufgabe nicht gefunden'}), 404

        task_data = safe_dict(task)
        task_data['examples'] = json.loads(task_data['examples'])
        task_data['hints'] = json.loads(task_data['hints'])
        task_data['test_cases'] = json.loads(task_data['test_cases'])

        return jsonify({'success': True, 'task': task_data}), 200

    except Exception as e:
        print(f"❌ Get task error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ai/validate-solution', methods=['POST'])
def ai_validate_solution():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        code = data.get('code', '')
        task_description = data.get('task_description', '')
        test_cases = data.get('test_cases', [])
        language = data.get('language', 'Python')

        if not task_id or not code:
            return jsonify({'success': False, 'message': 'Ungültige Daten'}), 400

        db = get_db()
        task = db.execute('SELECT * FROM ai_tasks WHERE task_id = ? AND user_id = ?',
                          (task_id, session['user_id'])).fetchone()

        if not task:
            db.close()
            return jsonify({'success': False, 'message': 'Aufgabe nicht gefunden'}), 404

        if task['completed']:
            db.close()
            return jsonify({'success': False, 'message': 'Bereits abgeschlossen'}), 400

        prompt = f"""Du bist ein erfahrener Programmierlehrer und Code-Reviewer. Analysiere die folgende Lösung.

Aufgabe: {task_description}
Programmiersprache: {language}

Testfälle:
{json.dumps(test_cases, ensure_ascii=False, indent=2)}

Schüler-Code:
```{language.lower()}
{code}
```

Überprüfe den Code auf:
1. Korrektheit - Erfüllt er die Aufgabe?
2. Syntax-Fehler
3. Logische Fehler
4. Best Practices

Antworte NUR mit JSON in diesem Format:
{{
  "is_correct": true/false,
  "errors": ["Fehler 1", "Fehler 2"],
  "suggestions": "Verbesserungsvorschläge hier",
  "feedback": "Positives Feedback oder Lob"
}}

Wenn der Code korrekt ist, setze "is_correct": true und "errors": [].
Wenn Fehler vorhanden sind, liste sie klar auf."""

        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system",
                     "content": "Du bist ein hilfreicher Code-Reviewer. Antworte NUR mit gültigem JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )

            response_text = completion.choices[0].message.content.strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()

            validation_result = json.loads(response_text)

            if validation_result.get('is_correct', False):
                task_dict = safe_dict(task)
                points_earned = task_dict['points_reward']

                db.execute('INSERT INTO ai_submissions (task_id, user_id, code, points_earned) VALUES (?, ?, ?, ?)',
                           (task_id, session['user_id'], code, points_earned))

                db.execute(
                    'UPDATE ai_tasks SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE task_id = ? AND user_id = ?',
                    (task_id, session['user_id']))

                db.execute('UPDATE users SET points = points + ? WHERE id = ?',
                           (points_earned, session['user_id']))

                db.execute('INSERT INTO points_history (user_id, points, reason, task_id) VALUES (?, ?, ?, ?)',
                           (session['user_id'], points_earned, f'AI Task: {task_dict["title"]}', task_id))

                db.commit()

                validation_result['points_earned'] = points_earned
                print(f"✅ Task completed: {task_dict['title']} (+{points_earned} points)")

            db.close()

            return jsonify({
                'success': True,
                'validation': validation_result
            }), 200

        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response text: {response_text}")
            return jsonify({
                'success': False,
                'message': 'AI-Antwort konnte nicht verarbeitet werden'
            }), 500

    except Exception as e:
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/ai/submit', methods=['POST'])
def ai_submit_solution():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

    try:
        data = request.get_json() or {}
        task_id = data.get('task_id')
        code = data.get('code', '')

        if not task_id or not code:
            return jsonify({'success': False, 'message': 'Ungültige Daten'}), 400

        db = get_db()
        task = db.execute('SELECT * FROM ai_tasks WHERE task_id = ? AND user_id = ?',
                          (task_id, session['user_id'])).fetchone()

        if not task:
            db.close()
            return jsonify({'success': False, 'message': 'Aufgabe nicht gefunden'}), 404

        if task['completed']:
            db.close()
            return jsonify({'success': False, 'message': 'Bereits abgeschlossen'}), 400

        task_dict = safe_dict(task)
        points_earned = task_dict['points_reward']

        db.execute('INSERT INTO ai_submissions (task_id, user_id, code, points_earned) VALUES (?, ?, ?, ?)',
                   (task_id, session['user_id'], code, points_earned))

        db.execute(
            'UPDATE ai_tasks SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE task_id = ? AND user_id = ?',
            (task_id, session['user_id']))

        db.execute('UPDATE users SET points = points + ? WHERE id = ?',
                   (points_earned, session['user_id']))

        db.execute('INSERT INTO points_history (user_id, points, reason, task_id) VALUES (?, ?, ?, ?)',
                   (session['user_id'], points_earned, f'Task: {task_dict["title"]}', task_id))

        db.commit()

        new_user = db.execute('SELECT points FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        db.close()

        total_points = safe_dict(new_user)['points'] if new_user else points_earned

        print(f"✅ Task abgeschlossen: {task_dict['title']} (+{points_earned} points)")

        return jsonify({
            'success': True,
            'message': f'Glückwunsch! +{points_earned} Punkte!',
            'points_earned': points_earned,
            'total_points': total_points
        }), 200

    except Exception as e:
        print(f"❌ Submit error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ FRIENDS SYSTEM ============

@app.route('/api/friends/search', methods=['GET'])
def search_users():
    if 'user_id' not in session:
        return jsonify([]), 401

    try:
        query = request.args.get('q', '').strip()
        if len(query) < 2:
            return jsonify([]), 200

        db = get_db()
        users = db.execute('''
                           SELECT u.id, u.name, u.email, u.points, p.avatar_url
                           FROM users u
                                    LEFT JOIN profiles p ON u.id = p.user_id
                           WHERE u.role = 'student'
                             AND u.id != ?
							 AND (u.name LIKE ? OR u.email LIKE ?)
						   LIMIT 10
                           ''', (session['user_id'], f'%{query}%', f'%{query}%')).fetchall()
        db.close()

        return jsonify([safe_dict(u) for u in users]), 200
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify([]), 500


@app.route('/api/friends/request', methods=['POST'])
def send_friend_request():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

    try:
        data = request.get_json() or {}
        friend_id = data.get('friend_id')

        if not friend_id or friend_id == session['user_id']:
            return jsonify({'success': False, 'message': 'Ungültige Anfrage'}), 400

        db = get_db()
        existing = db.execute('''
                              SELECT *
                              FROM friendships
                              WHERE (user_id = ? AND friend_id = ?)
                                 OR (user_id = ? AND friend_id = ?)
                              ''', (session['user_id'], friend_id, friend_id, session['user_id'])).fetchone()

        if existing:
            db.close()
            return jsonify({'success': False, 'message': 'Anfrage existiert bereits'}), 400

        db.execute('INSERT INTO friendships (user_id, friend_id, status) VALUES (?, ?, ?)',
                   (session['user_id'], friend_id, 'pending'))
        db.commit()
        db.close()

        return jsonify({'success': True, 'message': 'Anfrage gesendet!'}), 200
    except Exception as e:
        print(f"❌ Friend request error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/friends/accept', methods=['POST'])
def accept_friend_request():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

    try:
        data = request.get_json() or {}
        friend_id = data.get('friend_id')

        db = get_db()
        db.execute(
            'UPDATE friendships SET status = "accepted" WHERE user_id = ? AND friend_id = ? AND status = "pending"',
            (friend_id, session['user_id']))
        db.commit()
        db.close()

        return jsonify({'success': True, 'message': 'Freund hinzugefügt!'}), 200
    except Exception as e:
        print(f"❌ Accept friend error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/friends/list', methods=['GET'])
def get_friends():
    if 'user_id' not in session:
        return jsonify([]), 401

    try:
        db = get_db()
        friends = db.execute('''
                             SELECT u.id, u.name, u.points, p.avatar_url
                             FROM users u
                                      LEFT JOIN profiles p ON u.id = p.user_id
                             WHERE u.id IN (SELECT friend_id
                                            FROM friendships
                                            WHERE user_id = ?
                                              AND status = "accepted"
                                            UNION
                                            SELECT user_id
                                            FROM friendships
                                            WHERE friend_id = ?
                                              AND status = "accepted")
                             ORDER BY u.points DESC
                             ''', (session['user_id'], session['user_id'])).fetchall()
        db.close()

        return jsonify([safe_dict(f) for f in friends]), 200

    except Exception as e:
        print(f"❌ Get friends error: {e}")
        return jsonify([]), 500


@app.route('/api/friends/requests', methods=['GET'])
def get_friend_requests():
    if 'user_id' not in session:
        return jsonify([]), 401

    try:
        db = get_db()
        requests = db.execute('''
                              SELECT u.id, u.name, u.points, p.avatar_url, f.created_at
                              FROM friendships f
                                       JOIN users u ON f.user_id = u.id
                                       LEFT JOIN profiles p ON u.id = p.user_id
                              WHERE f.friend_id = ?
                                AND f.status = "pending"
                              ORDER BY f.created_at DESC
                              ''', (session['user_id'],)).fetchall()
        db.close()

        return jsonify([safe_dict(r) for r in requests]), 200
    except Exception as e:
        print(f"❌ Get requests error: {e}")
        return jsonify([]), 500


# ============ COURSES ============

@app.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        db = get_db()
        courses = db.execute('SELECT * FROM courses WHERE status = "active"').fetchall()
        db.close()

        # Add image_url to each course
        courses_list = []
        for c in courses:
            course_dict = safe_dict(c)
            # Добавляем изображения в зависимости от названия курса
            if 'Python' in course_dict.get('title', ''):
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=400&fit=crop'
            elif 'HTML' in course_dict.get('title', '') or 'CSS' in course_dict.get('title',
                                                                                    '') or 'Web' in course_dict.get(
                    'title', ''):
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1523437113738-bbd3cc89fb19?w=800&h=400&fit=crop'
            elif 'JavaScript' in course_dict.get('title', ''):
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&h=400&fit=crop'
            else:
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&h=400&fit=crop'

            courses_list.append(course_dict)

        return jsonify(courses_list), 200
    except Exception as e:
        print(f"❌ Get courses error: {e}")
        return jsonify([]), 500


# ============ COURSE DETAIL ============
@app.route('/api/courses/<int:course_id>', methods=['GET'])
def get_course_detail(course_id):
    """Get detailed information for a single course"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        db = get_db()

        # Get course information
        course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()

        if not course:
            db.close()
            return jsonify({'success': False, 'message': 'Course not found'}), 404

        course_dict = safe_dict(course)

        # Add image_url based on course title
        if 'Python' in course_dict.get('title', ''):
            course_dict[
                'image_url'] = 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=400&fit=crop'
        elif 'HTML' in course_dict.get('title', '') or 'CSS' in course_dict.get('title',
                                                                                '') or 'Web' in course_dict.get('title',
                                                                                                                ''):
            course_dict[
                'image_url'] = 'https://images.unsplash.com/photo-1523437113738-bbd3cc89fb19?w=800&h=400&fit=crop'
        elif 'JavaScript' in course_dict.get('title', ''):
            course_dict[
                'image_url'] = 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&h=400&fit=crop'
        else:
            course_dict[
                'image_url'] = 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&h=400&fit=crop'

        # Create lessons based on course title
        if 'Python' in course_dict.get('title', ''):
            # Python für Anfänger: 12 Lektionen, 6h total (30min each)
            lessons = [
                {
                    'id': 1,
                    'title': 'Einführung in Python',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Willkommen bei Python! 🐍</h3>
<p>Python ist eine der beliebtesten Programmiersprachen der Welt. Sie ist einfach zu lernen und wird von großen Unternehmen wie Google, Instagram und Netflix verwendet.</p>
<h4>Warum Python?</h4>
<ul>
<li>Einfache und lesbare Syntax</li>
<li>Vielseitig einsetzbar (Web, Data Science, KI)</li>
<li>Große Community und viele Bibliotheken</li>
</ul>
<h4>Installation</h4>
<p>Lade Python von <a href="https://python.org" target="_blank">python.org</a> herunter und installiere es. Überprüfe die Installation mit dem Befehl <code>python --version</code> in der Kommandozeile.</p>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=0&end=1800'
                },
                {
                    'id': 2,
                    'title': 'Variablen und Datentypen',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Variablen in Python</h3>
<p>Variablen sind wie Container für Daten. In Python musst du den Typ nicht angeben - Python erkennt ihn automatisch!</p>
<h4>Grundlegende Datentypen:</h4>
<ul>
<li><strong>int</strong> - Ganze Zahlen (z.B. 42, -17)</li>
<li><strong>float</strong> - Dezimalzahlen (z.B. 3.14, -0.5)</li>
<li><strong>str</strong> - Text (z.B. "Hallo Welt")</li>
<li><strong>bool</strong> - Wahr/Falsch (True/False)</li>
</ul>
<h4>Beispiel:</h4>
<pre><code>alter = 15
name = "Anna"
groesse = 1.65
ist_schueler = True</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=1800&end=3600'
                },
                {
                    'id': 3,
                    'title': 'Strings und Textverarbeitung',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Arbeiten mit Strings</h3>
<p>Strings sind Texte in Python. Sie sind sehr mächtig und haben viele nützliche Methoden!</p>
<h4>String-Operationen:</h4>
<ul>
<li><code>+</code> - Strings verbinden: <code>"Hallo" + " Welt"</code></li>
<li><code>*</code> - Strings wiederholen: <code>"Ha" * 3</code> ergibt "HaHaHa"</li>
<li><code>len()</code> - Länge ermitteln</li>
</ul>
<h4>String-Methoden:</h4>
<pre><code>text = "Python Programmierung"
print(text.upper())  # PYTHON PROGRAMMIERUNG
print(text.lower())  # python programmierung
print(text.split())  # ['Python', 'Programmierung']</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=3600&end=5400'
                },
                {
                    'id': 4,
                    'title': 'Listen und Tuples',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Listen in Python</h3>
<p>Listen sind Sammlungen von Elementen. Sie sind veränderbar und können verschiedene Datentypen enthalten.</p>
<h4>Listen erstellen:</h4>
<pre><code>fruechte = ["Apfel", "Banane", "Orange"]
zahlen = [1, 2, 3, 4, 5]
gemischt = [1, "Text", 3.14, True]</code></pre>
<h4>Listen-Operationen:</h4>
<ul>
<li><code>append()</code> - Element hinzufügen</li>
<li><code>remove()</code> - Element entfernen</li>
<li><code>sort()</code> - Liste sortieren</li>
<li><code>len()</code> - Anzahl der Elemente</li>
</ul>
<h4>Tuples:</h4>
<p>Tuples sind wie Listen, aber unveränderbar: <code>koordinaten = (10, 20)</code></p>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=5400&end=7200'
                },
                {
                    'id': 5,
                    'title': 'Dictionaries und Sets',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Dictionaries - Key-Value Paare</h3>
<p>Dictionaries speichern Daten in Schlüssel-Wert-Paaren. Perfekt für strukturierte Daten!</p>
<h4>Dictionary erstellen:</h4>
<pre><code>schueler = {
    "name": "Max",
    "alter": 14,
    "klasse": "8b"
}</code></pre>
<h4>Zugriff:</h4>
<pre><code>print(schueler["name"])  # Max
schueler["alter"] = 15   # Wert ändern</code></pre>
<h4>Sets:</h4>
<p>Sets sind ungeordnete Sammlungen ohne Duplikate: <code>hobbys = {"Lesen", "Sport"}</code></p>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=7200&end=9000'
                },
                {
                    'id': 6,
                    'title': 'If-Else Bedingungen',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Entscheidungen mit if-else</h3>
<p>Mit Bedingungen kann dein Programm unterschiedlich reagieren!</p>
<h4>Grundstruktur:</h4>
<pre><code>alter = 16
if alter >= 18:
    print("Volljährig")
elif alter >= 16:
    print("Roller fahren erlaubt")
else:
    print("Noch zu jung")</code></pre>
<h4>Operatoren:</h4>
<ul>
<li><code>==</code> gleich, <code>!=</code> ungleich</li>
<li><code>&gt;, &gt;=</code> größer (gleich)</li>
<li><code>&lt;, &lt;=</code> kleiner (gleich)</li>
</ul>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=9000&end=10800'
                },
                {
                    'id': 7,
                    'title': 'For Schleifen',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Wiederholungen mit for-Loops</h3>
<p>For-Schleifen durchlaufen Sequenzen Element für Element.</p>
<h4>Liste durchlaufen:</h4>
<pre><code>fruechte = ["Apfel", "Banane"]
for frucht in fruechte:
    print(f"Ich mag {frucht}")</code></pre>
<h4>Mit range():</h4>
<pre><code>for i in range(5):  # 0 bis 4
    print(i)

for i in range(1, 11):  # 1 bis 10
    print(f"{i} mal 2 = {i*2}")</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=10800&end=12600'
                },
                {
                    'id': 8,
                    'title': 'While Schleifen',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>While-Loops</h3>
<p>While-Schleifen laufen solange eine Bedingung True ist.</p>
<h4>Beispiel:</h4>
<pre><code>zaehler = 0
while zaehler < 5:
    print(f"Durchlauf {zaehler}")
    zaehler += 1</code></pre>
<h4>Mit break:</h4>
<pre><code>while True:
    antwort = input("Weiter? (j/n): ")
    if antwort == "n":
        break</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=12600&end=14400'
                },
                {
                    'id': 9,
                    'title': 'Funktionen',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Funktionen erstellen</h3>
<p>Funktionen sind wiederverwendbare Codeblöcke!</p>
<h4>Funktion definieren:</h4>
<pre><code>def begruessung(name):
    print(f"Hallo, {name}!")

begruessung("Anna")</code></pre>
<h4>Mit Rückgabewert:</h4>
<pre><code>def addiere(a, b):
    return a + b

ergebnis = addiere(5, 3)
print(ergebnis)  # 8</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=14400&end=16200'
                },
                {
                    'id': 10,
                    'title': 'Module und Imports',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Module verwenden</h3>
<p>Python hat viele nützliche Module!</p>
<h4>Standard-Module:</h4>
<pre><code>import math
print(math.pi)  # 3.14159...
print(math.sqrt(16))  # 4.0

import random
zahl = random.randint(1, 10)</code></pre>
<h4>Spezifische Imports:</h4>
<pre><code>from datetime import datetime
jetzt = datetime.now()
print(jetzt)</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=16200&end=18000'
                },
                {
                    'id': 11,
                    'title': 'Fehlerbehandlung',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Fehler behandeln</h3>
<p>Mit try-except Fehler abfangen!</p>
<h4>Beispiel:</h4>
<pre><code>try:
    zahl = int(input("Zahl: "))
    ergebnis = 100 / zahl
    print(ergebnis)
except ValueError:
    print("Keine Zahl!")
except ZeroDivisionError:
    print("Nicht durch 0!")</code></pre>
<h4>Mit finally:</h4>
<pre><code>try:
    datei = open("data.txt")
finally:
    datei.close()</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=18000&end=19800'
                },
                {
                    'id': 12,
                    'title': 'Praxis-Projekt',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Dein erstes Projekt! 🎉</h3>
<p>Wende alles Gelernte an!</p>
<h4>Projekt: Zahlenraten</h4>
<pre><code>import random

zahl = random.randint(1, 100)
versuche = 0

print("Ich denke an eine Zahl von 1-100!")

while True:
    tipp = int(input("Dein Tipp: "))
    versuche += 1

    if tipp < zahl:
        print("Zu niedrig!")
    elif tipp > zahl:
        print("Zu hoch!")
    else:
        print(f"Richtig in {versuche} Versuchen!")
        break</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/kqtD5dpn9C8'
                }
            ]
        elif 'HTML' in course_dict.get('title', '') or 'CSS' in course_dict.get('title',
                                                                                '') or 'Web' in course_dict.get('title',
                                                                                                                ''):
            # Webentwicklung mit HTML/CSS: 8 Lektionen, 4h total (30min average)
            lessons = [
                {
                    'id': 1,
                    'title': 'HTML Grundlagen - Einführung',
                    'duration': 20,
                    'completed': False,
                    'content': '''<h3>Willkommen zur Webentwicklung! 🌐</h3>
<p>HTML ist die Grundlage jeder Website!</p>
<h4>Grundstruktur:</h4>
<pre><code>&lt;!DOCTYPE html&gt;
&lt;html&gt;
&lt;head&gt;
    &lt;title&gt;Meine Seite&lt;/title&gt;
&lt;/head&gt;
&lt;body&gt;
    &lt;h1&gt;Hallo Welt!&lt;/h1&gt;
&lt;/body&gt;
&lt;/html&gt;</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/Q3MIitoSQkE'
                },
                {
                    'id': 2,
                    'title': 'HTML Vertiefung',
                    'duration': 35,
                    'completed': False,
                    'content': '''<h3>HTML Elemente</h3>
<h4>Text-Elemente:</h4>
<ul>
<li><code>&lt;h1&gt;</code>-<code>&lt;h6&gt;</code> Überschriften</li>
<li><code>&lt;p&gt;</code> Absätze</li>
<li><code>&lt;strong&gt;</code> Fetter Text</li>
</ul>
<h4>Links und Bilder:</h4>
<pre><code>&lt;a href="url"&gt;Link&lt;/a&gt;
&lt;img src="bild.jpg" alt="Text"&gt;</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/Q3MIitoSQkE'
                },
                {
                    'id': 3,
                    'title': 'HTML Praxis',
                    'duration': 25,
                    'completed': False,
                    'content': '''<h3>Deine erste Webseite!</h3>
<p>Erstelle eine persönliche Profilseite mit:</p>
<ul>
<li>Überschrift mit deinem Namen</li>
<li>Ein Bild</li>
<li>Absatz über dich</li>
<li>Liste deiner Hobbys</li>
</ul>
<h4>Beispiel:</h4>
<pre><code>&lt;h1&gt;Max Mustermann&lt;/h1&gt;
&lt;img src="profil.jpg"&gt;
&lt;p&gt;Ich lerne Programmieren!&lt;/p&gt;</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/Q3MIitoSQkE'
                },
                {
                    'id': 4,
                    'title': 'CSS Grundlagen - Teil 1',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Einführung in CSS</h3>
<p>CSS macht deine Webseite schön!</p>
<h4>CSS einbinden:</h4>
<pre><code>&lt;style&gt;
h1 {
    color: blue;
    font-size: 32px;
}
&lt;/style&gt;</code></pre>
<h4>Selektoren:</h4>
<ul>
<li>Element: <code>p { color: red; }</code></li>
<li>Klasse: <code>.wichtig { }</code></li>
<li>ID: <code>#header { }</code></li>
</ul>''',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=0&end=1200'
                },
                {
                    'id': 5,
                    'title': 'CSS Grundlagen - Teil 2',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Das Box Model</h3>
<p>Jedes Element ist eine Box!</p>
<h4>Komponenten:</h4>
<ul>
<li><strong>Content:</strong> Der Inhalt</li>
<li><strong>Padding:</strong> Innenabstand</li>
<li><strong>Border:</strong> Rahmen</li>
<li><strong>Margin:</strong> Außenabstand</li>
</ul>
<h4>Beispiel:</h4>
<pre><code>.box {
    padding: 20px;
    border: 2px solid black;
    margin: 10px;
}</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=600&end=1800'
                },
                {
                    'id': 6,
                    'title': 'CSS Layout - Flexbox',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Flexbox Layouts</h3>
<p>Flexbox ist perfekt für moderne Layouts!</p>
<h4>Container:</h4>
<pre><code>.container {
    display: flex;
    justify-content: center;
    align-items: center;
}</code></pre>
<h4>Navbar Beispiel:</h4>
<pre><code>.navbar {
    display: flex;
    justify-content: space-between;
}</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=1200&end=2400'
                },
                {
                    'id': 7,
                    'title': 'CSS Positionierung',
                    'duration': 30,
                    'completed': False,
                    'content': '''<h3>Position Eigenschaften</h3>
<h4>Arten:</h4>
<ul>
<li><strong>static:</strong> Normal (Standard)</li>
<li><strong>relative:</strong> Relativ zur normalen Position</li>
<li><strong>absolute:</strong> Absolut positioniert</li>
<li><strong>fixed:</strong> Fest im Viewport</li>
</ul>
<h4>Fixed Header:</h4>
<pre><code>.header {
    position: fixed;
    top: 0;
    width: 100%;
}</code></pre>''',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=1800&end=3000'
                },
                {
                    'id': 8,
                    'title': 'CSS & HTML Projekt',
                    'duration': 40,
                    'completed': False,
                    'content': '''<h3>Abschlussprojekt! 🎨</h3>
<p>Erstelle eine komplette Website!</p>
<h4>Anforderungen:</h4>
<ul>
<li>Header mit Navigation</li>
<li>Hero-Section mit Bild</li>
<li>3 Cards mit Inhalt</li>
<li>Footer mit Links</li>
</ul>
<h4>Responsive Design:</h4>
<pre><code>@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }
}</code></pre>
<p>Viel Erfolg! 🚀</p>''',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y'
                }
            ]
        else:
            # Default lessons for other courses
            lessons = [
                {
                    'id': 1,
                    'title': 'Einführung',
                    'duration': 30,
                    'completed': False,
                    'content': 'Einführung in das Thema.',
                    'video_url': 'https://www.youtube.com/embed/kqtD5dpn9C8'
                },
                {
                    'id': 2,
                    'title': 'Grundlagen',
                    'duration': 30,
                    'completed': False,
                    'content': 'Lerne die Grundlagen kennen.',
                    'video_url': 'https://www.youtube.com/embed/kqtD5dpn9C8'
                }
            ]

        course_dict['lessons'] = lessons
        course_dict['quiz'] = {'id': f'quiz_{course_id}'}

        db.close()

        return jsonify({'success': True, 'course': course_dict}), 200

    except Exception as e:
        print(f"❌ Get course detail error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ MY COURSES ============
@app.route('/api/my-courses', methods=['GET'])
def get_my_courses():
    if 'user_id' not in session:
        return jsonify([]), 200

    try:
        db = get_db()
        rows = db.execute('''
                          SELECT c.*
                          FROM courses c
                                   JOIN enrollments e ON c.id = e.course_id
                          WHERE e.user_id = ?
                          ''', (session['user_id'],)).fetchall()
        db.close()

        # Add image_url to each course
        courses_list = []
        for r in rows:
            course_dict = safe_dict(r)
            # Add image_url based on course title
            if 'Python' in course_dict.get('title', ''):
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=400&fit=crop'
            elif 'HTML' in course_dict.get('title', '') or 'CSS' in course_dict.get('title',
                                                                                    '') or 'Web' in course_dict.get(
                    'title', ''):
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1523437113738-bbd3cc89fb19?w=800&h=400&fit=crop'
            elif 'JavaScript' in course_dict.get('title', ''):
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&h=400&fit=crop'
            else:
                course_dict[
                    'image_url'] = 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&h=400&fit=crop'

            courses_list.append(course_dict)

        return jsonify(courses_list), 200
    except Exception as e:
        print(f"❌ Get my courses error: {e}")
        return jsonify([]), 500


@app.route('/api/enroll', methods=['POST'])
def enroll_course():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    data = request.get_json() or {}
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({"success": False, "message": "Course ID missing"}), 400

    try:
        db = get_db()

        existing = db.execute(
            "SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?",
            (session['user_id'], course_id)
        ).fetchone()

        if existing:
            db.close()
            return jsonify({"success": False, "message": "Already enrolled"}), 400

        db.execute(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            (session['user_id'], course_id)
        )
        db.commit()
        db.close()

        return jsonify({"success": True, "message": "Successfully enrolled"}), 200
    except Exception as e:
        print(f"❌ Enroll error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/unenroll', methods=['POST'])
def unenroll_course():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Not authenticated"}), 401

    data = request.get_json() or {}
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({"success": False, "message": "Course ID missing"}), 400

    try:
        db = get_db()

        existing = db.execute(
            "SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?",
            (session['user_id'], course_id)
        ).fetchone()

        if not existing:
            db.close()
            return jsonify({"success": False, "message": "Not enrolled in this course"}), 400

        db.execute(
            "DELETE FROM enrollments WHERE user_id = ? AND course_id = ?",
            (session['user_id'], course_id)
        )
        db.commit()
        db.close()

        return jsonify({"success": True, "message": "Successfully unenrolled"}), 200
    except Exception as e:
        print(f"❌ Unenroll error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


# ============ QUIZ SYSTEM ============
# ============ QUIZ SYSTEM ============

class QuizGenerator:
    def __init__(self, course_title, course_description):
        self.course_title = course_title
        self.course_description = course_description

    def generate_quiz(self, num_questions=10, user_id=None, difficulty="medium"):
        """Generate quiz using Groq AI with randomization and difficulty"""
        print(f"🎯 Starting quiz generation: {num_questions} questions, difficulty: {difficulty}")

        try:
            # Add randomization seed based on timestamp and user_id
            import time
            seed = int(time.time() * 1000) + (user_id or 0)
            print(f"🎲 Seed: {seed}")

            # Difficulty descriptions for AI
            difficulty_map = {
                "easy": "einfach - Grundlegende Konzepte, direkte Fragen",
                "medium": "mittel - Anwendung von Konzepten, einige Denkaufgaben",
                "hard": "schwer - Komplexe Probleme, fortgeschrittene Konzepte",
                "adaptive": "gemischt - Verschiedene Schwierigkeitsgrade"
            }

            difficulty_desc = difficulty_map.get(difficulty, difficulty_map["medium"])

            # Calculate code vs multiple choice split
            num_code = int(num_questions * 0.4)  # 40% code
            num_multiple = num_questions - num_code  # 60% multiple choice

            prompt = f"""Du bist ein Experte für Bildungsinhalte. Erstelle ein EINZIGARTIGES Quiz mit GENAU {num_questions} Fragen zum Thema: "{self.course_title}".

Kurs-Beschreibung: {self.course_description}

Schwierigkeitsgrad: {difficulty_desc}
Randomization Seed: {seed}

WICHTIG - ANZAHL DER FRAGEN:
- Erstelle GENAU {num_questions} Fragen (nicht mehr, nicht weniger)
- Davon {num_multiple} Multiple-Choice Fragen
- Davon {num_code} Code-Übungen

Erstelle ein JSON-Objekt mit folgendem Format:
{{
    "questions": [
        {{
            "id": 1,
            "type": "multiple_choice",
            "difficulty": "easy",
            "question": "Frage Text hier?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Erklärung warum diese Antwort richtig ist"
        }},
        {{
            "id": 2,
            "type": "code",
            "difficulty": "medium",
            "question": "Finde und korrigiere den Fehler im folgenden Code:",
            "code": "def add(a, b):\\n    return a - b",
            "options": ["return a + b", "return a * b", "return a / b", "return a - b"],
            "correct_answer": 0,
            "explanation": "Die Funktion sollte addieren, nicht subtrahieren"
        }}
    ]
}}

KRITISCHE ANFORDERUNGEN:
- GENAU {num_questions} Fragen erstellen
- Passe die Schwierigkeit an: {difficulty_desc}
- Jede Frage MUSS ein "difficulty" Feld haben: "easy", "medium", oder "hard"
- Für Code-Fragen: MUSS ein "code" Feld mit dem Code-Beispiel haben
- Nutze den Seed {seed} um UNTERSCHIEDLICHE Fragen zu generieren
- KEINE sich wiederholenden Fragen
- Explanationen sollen lehrreich und detailliert sein
- Alle Texte auf Deutsch
- NUR JSON zurückgeben, KEINE zusätzlichen Texte, KEINE Markdown-Formatierung
"""

            print(f"🤖 Calling Groq API...")
            print(f"📊 Course: {self.course_title}")
            print(f"📊 Requesting: {num_questions} questions ({num_multiple} MC, {num_code} code)")

            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein professioneller Quiz-Generator. Generiere IMMER unterschiedliche Fragen. Antworte NUR mit validem JSON ohne Markdown-Formatierung."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.9,
                max_tokens=4000,
                top_p=0.95
            )

            response_text = response.choices[0].message.content.strip()
            print(f"📝 Raw API response length: {len(response_text)} characters")
            print(f"📝 First 200 chars: {response_text[:200]}")

            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
                print("🔧 Removed ```json prefix")
            if response_text.startswith('```'):
                response_text = response_text[3:]
                print("🔧 Removed ``` prefix")
            if response_text.endswith('```'):
                response_text = response_text[:-3]
                print("🔧 Removed ``` suffix")
            response_text = response_text.strip()

            print(f"📝 Cleaned response length: {len(response_text)} characters")
            print(f"📝 Attempting JSON parse...")

            try:
                quiz_data = json.loads(response_text)
                print(f"✅ JSON parsed successfully!")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing FAILED!")
                print(f"❌ Error: {e}")
                print(f"❌ Error position: line {e.lineno}, column {e.colno}")
                print(f"❌ Full response:")
                print("=" * 80)
                print(response_text)
                print("=" * 80)
                raise

            # Validate question count
            actual_count = len(quiz_data.get('questions', []))
            print(f"✅ Generated {actual_count} questions (requested: {num_questions})")

            if actual_count < num_questions:
                print(f"⚠️ Warning: Only got {actual_count} questions, expected {num_questions}")

            # Add unique IDs and ensure difficulty field exists
            for i, question in enumerate(quiz_data['questions']):
                question['id'] = i + 1
                if 'difficulty' not in question:
                    question['difficulty'] = difficulty
                if 'type' not in question:
                    question['type'] = 'multiple_choice'

            print(f"✅ Quiz generation successful!")
            return quiz_data

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"❌ Falling back to default quiz")
            import traceback
            traceback.print_exc()
            return self._get_fallback_quiz(num_questions, difficulty)
        except Exception as e:
            print(f"❌ Quiz generation error: {e}")
            print(f"❌ Falling back to default quiz")
            import traceback
            traceback.print_exc()
            return self._get_fallback_quiz(num_questions, difficulty)

    def _get_fallback_quiz(self, num_questions=10, difficulty="medium"):
        """Fallback quiz if AI generation fails"""
        print(f"⚠️ Using fallback quiz with {num_questions} questions")

        # Generate fallback questions based on requested count
        questions = []
        for i in range(num_questions):
            if i % 2 == 0:  # Multiple choice
                questions.append({
                    "id": i + 1,
                    "type": "multiple_choice",
                    "difficulty": difficulty,
                    "question": f"Fallback Frage {i + 1}: Was ist das Hauptthema von {self.course_title}?",
                    "options": [
                        "Programmierung",
                        "Mathematik",
                        "Geschichte",
                        "Kunst"
                    ],
                    "correct_answer": 0,
                    "explanation": "Dies ist eine Fallback-Frage."
                })
            else:  # Code question
                questions.append({
                    "id": i + 1,
                    "type": "code",
                    "difficulty": difficulty,
                    "question": f"Fallback Code-Frage {i + 1}: Was ist die Ausgabe?",
                    "code": "x = 5\nprint(x + 3)",
                    "options": [
                        "8",
                        "53",
                        "5 + 3",
                        "Error"
                    ],
                    "correct_answer": 0,
                    "explanation": "5 + 3 = 8"
                })

        return {"questions": questions}


def generate_ai_feedback(score, correct, total, difficulty, course_title):
    """Generate personalized AI feedback based on quiz performance"""
    try:
        prompt = f"""Du bist ein erfahrener Programmierlehrer. Ein Schüler hat gerade ein Quiz zum Thema "{course_title}" abgeschlossen.

Ergebnisse:
- Punkte: {score}%
- Richtig: {correct} von {total}
- Schwierigkeitsgrad: {difficulty}

Erstelle personalisiertes Feedback mit:
1. Lob für gute Leistung oder Ermutigung
2. Konkrete Verbesserungsvorschläge
3. Empfehlung für nächste Schritte
4. Vorschlag für Schwierigkeitsgrad beim nächsten Quiz

Antworte NUR mit JSON:
{{
  "message": "Dein Feedback hier (2-3 Sätze)",
  "suggestions": ["Tipp 1", "Tipp 2"],
  "next_difficulty": "easy/medium/hard",
  "next_steps": "Was der Schüler als nächstes tun sollte"
}}
"""

        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Du bist ein motivierender Programmierlehrer. Gib konstruktives Feedback. Antworte NUR mit JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        response_text = response.choices[0].message.content.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()

        feedback_data = json.loads(response_text)
        return json.dumps(feedback_data, ensure_ascii=False)

    except Exception as e:
        print(f"❌ AI feedback error: {e}")
        # Fallback feedback
        if score >= 80:
            return json.dumps({
                "message": "Ausgezeichnet! Du hast das Quiz sehr gut gemeistert!",
                "suggestions": ["Versuche den nächsten Schwierigkeitsgrad"],
                "next_difficulty": "hard",
                "next_steps": "Fordere dich mit schwierigeren Aufgaben heraus"
            }, ensure_ascii=False)
        elif score >= 60:
            return json.dumps({
                "message": "Gut gemacht! Du hast bestanden!",
                "suggestions": ["Wiederhole die schwierigeren Themen"],
                "next_difficulty": "medium",
                "next_steps": "Übe weiter um sicherer zu werden"
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "message": "Nicht aufgeben! Übung macht den Meister!",
                "suggestions": ["Schaue die Videos nochmal an", "Beginne mit einfacheren Aufgaben"],
                "next_difficulty": "easy",
                "next_steps": "Wiederhole die Grundlagen"
            }, ensure_ascii=False)


@app.route('/api/quizzes/<quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    """Get or generate a NEW quiz for a course"""
    print(f"🎓 Quiz request received: {quiz_id}")

    if 'user_id' not in session:
        print("❌ User not authenticated")
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        # Extract course_id from quiz_id (format: quiz_1)
        course_id = int(quiz_id.replace('quiz_', ''))

        # Get parameters from query string
        num_questions = int(request.args.get('count', 10))
        difficulty = request.args.get('difficulty', 'medium')

        print(f"📚 Course ID: {course_id}, Questions: {num_questions}, Difficulty: {difficulty}")

        db = get_db()

        # Get course info
        course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()

        if not course:
            db.close()
            print(f"❌ Course not found: {course_id}")
            return jsonify({'success': False, 'message': 'Course not found'}), 404

        course_dict = safe_dict(course)

        # If adaptive difficulty, calculate based on history
        if difficulty == 'adaptive':
            # Get last quiz performance
            last_quiz = db.execute('''
                                   SELECT qa.score
                                   FROM quiz_answers qa
                                            JOIN quizzes q ON qa.quiz_id = q.id
                                   WHERE q.course_id = ?
                                     AND q.user_id = ?
                                   ORDER BY qa.submitted_at DESC LIMIT 1
                                   ''', (course_id, session['user_id'])).fetchone()

            if last_quiz:
                score = last_quiz['score']
                if score >= 80:
                    difficulty = 'hard'
                    print(f"🤖 AI chose: HARD (last score: {score}%)")
                elif score >= 60:
                    difficulty = 'medium'
                    print(f"🤖 AI chose: MEDIUM (last score: {score}%)")
                else:
                    difficulty = 'easy'
                    print(f"🤖 AI chose: EASY (last score: {score}%)")
            else:
                difficulty = 'medium'
                print(f"🤖 AI chose: MEDIUM (first attempt)")

        # Count how many attempts user has made
        attempt_count = db.execute('''
                                   SELECT COUNT(*) as count
                                   FROM quizzes
                                   WHERE course_id = ? AND user_id = ?
                                   ''', (course_id, session['user_id'])).fetchone()['count']

        new_attempt_number = attempt_count + 1

        # Generate new quiz using AI
        print(f"🤖 Generating quiz attempt #{new_attempt_number}")
        generator = QuizGenerator(
            course_title=course_dict['title'],
            course_description=course_dict['description']
        )

        quiz_data = generator.generate_quiz(
            num_questions=num_questions,
            user_id=session['user_id'],
            difficulty=difficulty
        )

        # Save NEW quiz to database
        cursor = db.execute('''
                            INSERT INTO quizzes (course_id, user_id, title, questions_json, attempt_number, created_at)
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                            ''', (
                                course_id,
                                session['user_id'],
                                f"Quiz: {course_dict['title']} - Versuch {new_attempt_number}",
                                json.dumps(quiz_data, ensure_ascii=False),
                                new_attempt_number
                            ))
        new_quiz_id = cursor.lastrowid
        db.commit()
        db.close()

        print(f"✅ Quiz #{new_attempt_number} generated ({num_questions} questions, {difficulty})")

        return jsonify({
            'success': True,
            'quiz': {
                'id': f'quiz_{course_id}_{new_quiz_id}',
                'db_id': new_quiz_id,
                'title': f"Quiz: {course_dict['title']} - Versuch {new_attempt_number}",
                'attempt_number': new_attempt_number,
                'difficulty': difficulty,
                'questions': quiz_data['questions']
            }
        }), 200

    except Exception as e:
        print(f"❌ Get quiz error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/quizzes/<quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    """Submit quiz answers and get results"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        user_answers = data.get('answers', {})
        db_quiz_id = data.get('db_id')  # Get the database quiz ID

        if not db_quiz_id:
            # Fallback: try to get the latest quiz for this course
            course_id = int(quiz_id.split('_')[1])
            db = get_db()
            latest_quiz = db.execute('''
                                     SELECT *
                                     FROM quizzes
                                     WHERE course_id = ?
                                       AND user_id = ?
                                     ORDER BY created_at DESC LIMIT 1
                                     ''', (course_id, session['user_id'])).fetchone()

            if not latest_quiz:
                db.close()
                return jsonify({'success': False, 'message': 'Quiz not found'}), 404

            db_quiz_id = latest_quiz['id']

        db = get_db()

        # Get quiz
        quiz = db.execute('SELECT * FROM quizzes WHERE id = ?', (db_quiz_id,)).fetchone()

        if not quiz:
            db.close()
            return jsonify({'success': False, 'message': 'Quiz not found'}), 404

        # Get course info for feedback
        course = db.execute('SELECT * FROM courses WHERE id = ?', (quiz['course_id'],)).fetchone()
        course_dict = safe_dict(course)

        quiz_data = json.loads(quiz['questions_json'])
        questions = quiz_data['questions']

        # Calculate score
        correct = 0
        total = len(questions)
        results = []

        for question in questions:
            q_id = str(question['id'])
            user_answer = user_answers.get(q_id)
            correct_answer = question['correct_answer']

            is_correct = user_answer == correct_answer
            if is_correct:
                correct += 1

            results.append({
                'question_id': question['id'],
                'correct': is_correct,
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'explanation': question['explanation']
            })

        score = int((correct / total) * 100)
        passed = score >= 60  # 60% passing score

        # Generate AI feedback based on performance
        feedback = generate_ai_feedback(
            score=score,
            correct=correct,
            total=total,
            difficulty='medium',  # You can get this from quiz data if stored
            course_title=course_dict['title']
        )

        # Save result to database with feedback
        db.execute('''
                   INSERT INTO quiz_answers (quiz_id, user_id, answers_json, score, passed, feedback, submitted_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                   ''', (
                       db_quiz_id,
                       session['user_id'],
                       json.dumps(user_answers),
                       score,
                       1 if passed else 0,
                       feedback
                   ))
        db.commit()

        # Award points if passed
        if passed:
            points_earned = 500
            db.execute('UPDATE users SET points = points + ? WHERE id = ?',
                       (points_earned, session['user_id']))
            db.execute('INSERT INTO points_history (user_id, points, reason) VALUES (?, ?, ?)',
                       (session['user_id'], points_earned, f'Quiz bestanden: {quiz["title"]}'))
            db.commit()
            print(f"✅ Quiz passed! +{points_earned} points")

        db.close()

        return jsonify({
            'success': True,
            'score': score,
            'correct': correct,
            'total': total,
            'passed': passed,
            'passing_score': 60,
            'results': results,
            'attempt_number': quiz['attempt_number'],
            'ai_feedback': feedback
        }), 200

    except Exception as e:
        print(f"❌ Submit quiz error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/quizzes/history/<int:course_id>', methods=['GET'])
def get_quiz_history(course_id):
    """Get quiz history for a course"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401

    try:
        db = get_db()

        # Get all quiz attempts with their results
        history = db.execute('''
                             SELECT q.id,
                                    q.title,
                                    q.attempt_number,
                                    q.created_at,
                                    qa.score,
                                    qa.passed,
                                    qa.feedback,
                                    qa.submitted_at
                             FROM quizzes q
                                      LEFT JOIN quiz_answers qa ON q.id = qa.quiz_id
                             WHERE q.course_id = ?
                               AND q.user_id = ?
                             ORDER BY q.created_at DESC
                             ''', (course_id, session['user_id'])).fetchall()

        db.close()

        history_list = []
        for item in history:
            history_list.append({
                'id': item['id'],
                'title': item['title'],
                'attempt_number': item['attempt_number'],
                'created_at': item['created_at'],
                'score': item['score'],
                'passed': item['passed'],
                'feedback': item['feedback'],
                'submitted_at': item['submitted_at']
            })

        return jsonify({
            'success': True,
            'history': history_list
        }), 200

    except Exception as e:
        print(f"❌ Get quiz history error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ STUDENT ASSIGNMENTS (PDF-BASED QUIZZES) ============
@app.route('/api/student/teacher-assignments', methods=['GET'])
def get_student_teacher_assignments():
    """Get all teacher-created PDF-based quizzes for students"""
    if 'user_id' not in session or session.get('user_role') != 'student':
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        db = get_db()

        # Get all quizzes created by teachers (PDF-based quizzes)
        assignments = db.execute('''
                                 SELECT q.id,
                                        q.title,
                                        q.created_at,
                                        q.course_id,
                                        c.title as course_title,
                                        c.color as course_color,
                                        u.name  as teacher_name,
                                        u.id    as teacher_id,
                                        qp.filename,
                                        qa.id   as answer_id,
                                        qa.score,
                                        qa.passed,
                                        qa.submitted_at
                                 FROM quizzes q
                                          INNER JOIN quiz_pdfs qp ON q.id = qp.quiz_id
                                          INNER JOIN courses c ON q.course_id = c.id
                                          INNER JOIN users u ON q.user_id = u.id
                                          LEFT JOIN quiz_answers qa ON q.id = qa.quiz_id AND qa.user_id = ?
                                 WHERE u.role = 'teacher'
                                 ORDER BY q.created_at DESC
                                 ''', (session['user_id'],)).fetchall()

        db.close()

        assignments_list = []
        for assignment in assignments:
            assignment_dict = safe_dict(assignment)

            # Check if completed
            completed = assignment_dict.get('answer_id') is not None
            assignment_dict['completed'] = completed

            if completed:
                assignment_dict['score'] = assignment_dict.get('score', 0)
                assignment_dict['passed'] = assignment_dict.get('passed', 0) == 1
            else:
                assignment_dict['score'] = None
                assignment_dict['passed'] = None

            assignments_list.append(assignment_dict)

        print(f"✅ Loaded {len(assignments_list)} teacher assignments for student")
        return jsonify({'success': True, 'assignments': assignments_list}), 200

    except Exception as e:
        print(f"❌ Get teacher assignments error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e), 'assignments': []}), 500


@app.route('/api/student/assignment/<int:assignment_id>', methods=['GET'])
def get_student_assignment(assignment_id):
    """Get a specific teacher-created assignment/quiz for student"""
    if 'user_id' not in session or session.get('user_role') != 'student':
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        db = get_db()

        # Get quiz details
        quiz = db.execute('''
                          SELECT q.id,
                                 q.title,
                                 q.questions_json,
                                 q.created_at,
                                 q.course_id,
                                 c.title as course_title,
                                 c.color as course_color,
                                 u.name  as teacher_name,
                                 qp.filename
                          FROM quizzes q
                                   INNER JOIN quiz_pdfs qp ON q.id = qp.quiz_id
                                   INNER JOIN courses c ON q.course_id = c.id
                                   INNER JOIN users u ON q.user_id = u.id
                          WHERE q.id = ?
                            AND u.role = 'teacher'
                          ''', (assignment_id,)).fetchone()

        if not quiz:
            db.close()
            return jsonify({'success': False, 'message': 'Aufgabe nicht gefunden'}), 404

        # Parse questions
        try:
            questions_data = json.loads(quiz['questions_json'])
            questions = questions_data.get('questions', [])
        except:
            questions = []

        quiz_dict = safe_dict(quiz)
        quiz_dict['questions'] = questions
        quiz_dict.pop('questions_json', None)

        db.close()

        print(f"✅ Loaded assignment {assignment_id} for student")
        return jsonify({
            'success': True,
            'quiz': quiz_dict
        }), 200

    except Exception as e:
        print(f"❌ Get assignment error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ PROFILE ============
@app.route('/api/profile', methods=['GET', 'PUT'])
def profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

    db = get_db()
    try:
        if request.method == 'GET':
            profile = db.execute('SELECT * FROM profiles WHERE user_id = ?', (session['user_id'],)).fetchone()
            db.close()
            if not profile:
                return jsonify({}), 200
            profile_dict = safe_dict(profile)
            return jsonify(profile_dict), 200

        elif request.method == 'PUT':
            data = request.get_json() or {}
            db.execute('''
                       UPDATE profiles
                       SET avatar_url          = ?,
                           birthdate           = ?,
                           country             = ?,
                           bio                 = ?,
                           favorite_language   = ?,
                           experience_level    = ?,
                           profile_visible     = ?,
                           friend_requests     = ?,
                           email_notifications = ?,
                           updated_at          = CURRENT_TIMESTAMP
                       WHERE user_id = ?
                       ''', (
                           data.get('avatar_url'),
                           data.get('birthdate'),
                           data.get('country'),
                           data.get('bio'),
                           data.get('favorite_language'),
                           data.get('experience_level'),
                           int(data.get('profile_visible', True)),
                           int(data.get('friend_requests', True)),
                           int(data.get('email_notifications', True)),
                           session['user_id']
                       ))
            db.commit()
            db.close()
            return jsonify({'success': True, 'message': 'Profil erfolgreich gespeichert'}), 200

    except Exception as e:
        db.close()
        print(f"❌ Profile error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============ TEACHER QUIZ RESULTS ENDPOINTS ============
@app.route('/api/teacher/quiz-results', methods=['GET'])
def get_teacher_quiz_results():
    """Get all quiz results for teacher dashboard"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        db = get_db()
        results = db.execute('''
                             SELECT qa.id,
                                    qa.quiz_id,
                                    qa.user_id,
                                    qa.score,
                                    qa.passed,
                                    qa.feedback,
                                    qa.submitted_at,
                                    u.name                                                            as student_name,
                                    u.email                                                           as student_email,
                                    u.points                                                          as student_points,
                                    p.avatar_url                                                      as student_avatar,
                                    q.title                                                           as quiz_title,
                                    q.attempt_number,
                                    q.course_id,
                                    c.title                                                           as course_title,
                                    (SELECT COUNT(*) FROM json_each(q.questions_json, '$.questions')) as total_questions
                             FROM quiz_answers qa
                                      JOIN users u ON qa.user_id = u.id
                                      LEFT JOIN profiles p ON u.id = p.user_id
                                      JOIN quizzes q ON qa.quiz_id = q.id
                                      JOIN courses c ON q.course_id = c.id
                             WHERE u.role = 'student'
                             ORDER BY qa.submitted_at DESC
                             ''').fetchall()
        db.close()

        results_list = []
        for result in results:
            result_dict = safe_dict(result)
            if result_dict.get('feedback'):
                try:
                    result_dict['feedback_parsed'] = json.loads(result_dict['feedback'])
                except:
                    result_dict['feedback_parsed'] = None
            if result_dict.get('total_questions') and result_dict.get('score') is not None:
                result_dict['correct_answers'] = round((result_dict['score'] / 100) * result_dict['total_questions'])
            results_list.append(result_dict)

        print(f"✅ Loaded {len(results_list)} quiz results for teacher")
        return jsonify({'success': True, 'results': results_list}), 200

    except Exception as e:
        print(f"❌ Get quiz results error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/teacher/student/<int:student_id>/quiz-results', methods=['GET'])
def get_student_quiz_results(student_id):
    """Get quiz results for a specific student"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        db = get_db()
        student = db.execute(
            'SELECT u.*, p.avatar_url FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.id = ? AND u.role = "student"',
            (student_id,)).fetchone()

        if not student:
            db.close()
            return jsonify({'success': False, 'message': 'Student nicht gefunden'}), 404

        results = db.execute('''
                             SELECT qa.id,
                                    qa.quiz_id,
                                    qa.score,
                                    qa.passed,
                                    qa.feedback,
                                    qa.submitted_at,
                                    qa.answers_json,
                                    q.title    as quiz_title,
                                    q.attempt_number,
                                    q.questions_json,
                                    q.course_id,
                                    c.title    as course_title,
                                    c.category as course_category
                             FROM quiz_answers qa
                                      JOIN quizzes q ON qa.quiz_id = q.id
                                      JOIN courses c ON q.course_id = c.id
                             WHERE qa.user_id = ?
                             ORDER BY qa.submitted_at DESC
                             ''', (student_id,)).fetchall()
        db.close()

        student_dict = safe_dict(student)
        results_list = []

        for result in results:
            result_dict = safe_dict(result)
            try:
                questions_data = json.loads(result_dict['questions_json'])
                result_dict['total_questions'] = len(questions_data.get('questions', []))
                result_dict['correct_answers'] = round((result_dict['score'] / 100) * result_dict['total_questions'])
            except:
                result_dict['total_questions'] = 0
                result_dict['correct_answers'] = 0
            result_dict.pop('questions_json', None)
            result_dict.pop('answers_json', None)
            results_list.append(result_dict)

        total_quizzes = len(results_list)
        passed_quizzes = len([r for r in results_list if r.get('passed')])
        avg_score = sum([r.get('score', 0) for r in results_list]) / total_quizzes if total_quizzes > 0 else 0

        return jsonify({
            'success': True,
            'student': student_dict,
            'results': results_list,
            'statistics': {
                'total_quizzes': total_quizzes,
                'passed_quizzes': passed_quizzes,
                'failed_quizzes': total_quizzes - passed_quizzes,
                'average_score': round(avg_score, 1),
                'pass_rate': round((passed_quizzes / total_quizzes * 100), 1) if total_quizzes > 0 else 0
            }
        }), 200

    except Exception as e:
        print(f"❌ Get student quiz results error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/teacher/quiz/<int:quiz_id>/details', methods=['GET'])
def get_quiz_details(quiz_id):
    """Get detailed quiz information"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        db = get_db()
        quiz = db.execute('''
                          SELECT q.*,
                                 u.name  as student_name,
                                 u.email as student_email,
                                 c.title as course_title,
                                 qa.score,
                                 qa.passed,
                                 qa.submitted_at,
                                 qa.answers_json,
                                 qa.feedback
                          FROM quizzes q
                                   JOIN users u ON q.user_id = u.id
                                   JOIN courses c ON q.course_id = c.id
                                   LEFT JOIN quiz_answers qa ON q.id = qa.quiz_id
                          WHERE q.id = ?
                          ''', (quiz_id,)).fetchone()
        db.close()

        if not quiz:
            return jsonify({'success': False, 'message': 'Quiz nicht gefunden'}), 404

        quiz_dict = safe_dict(quiz)
        try:
            questions_data = json.loads(quiz_dict['questions_json'])
            quiz_dict['questions'] = questions_data.get('questions', [])

            if quiz_dict.get('answers_json'):
                user_answers = json.loads(quiz_dict['answers_json'])
                for question in quiz_dict['questions']:
                    q_id = str(question['id'])
                    user_answer_idx = user_answers.get(q_id)
                    question['user_answer'] = user_answer_idx
                    question['user_answer_text'] = question['options'][
                        user_answer_idx] if user_answer_idx is not None else None
                    question['correct_answer_text'] = question['options'][question['correct_answer']]
                    question['is_correct'] = user_answer_idx == question['correct_answer']

            if quiz_dict.get('feedback'):
                quiz_dict['feedback_parsed'] = json.loads(quiz_dict['feedback'])
        except Exception as e:
            print(f"⚠️ Error parsing quiz details: {e}")
            quiz_dict['questions'] = []

        quiz_dict.pop('questions_json', None)
        quiz_dict.pop('answers_json', None)
        return jsonify({'success': True, 'quiz': quiz_dict}), 200

    except Exception as e:
        print(f"❌ Get quiz details error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# Add these endpoints to app.py

@app.route('/api/teacher/quiz/<int:quiz_id>/delete', methods=['DELETE'])
def delete_teacher_quiz(quiz_id):
    """Delete a quiz created by teacher"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        db = get_db()

        # Verify quiz belongs to this teacher
        quiz = db.execute('''
                          SELECT *
                          FROM quizzes
                          WHERE id = ?
                            AND user_id = ?
                          ''', (quiz_id, session['user_id'])).fetchone()

        if not quiz:
            db.close()
            return jsonify({'success': False, 'message': 'Quiz nicht gefunden'}), 404

        # Delete quiz (cascade will delete answers and pdf metadata)
        db.execute('DELETE FROM quizzes WHERE id = ?', (quiz_id,))
        db.commit()
        db.close()

        print(f"✅ Quiz deleted: {quiz_id}")
        return jsonify({'success': True, 'message': 'Quiz gelöscht'}), 200

    except Exception as e:
        print(f"❌ Delete quiz error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/teacher/pdf-quizzes', methods=['GET'])
def get_teacher_pdf_quizzes():
    """Get all PDF-based quizzes for teacher dashboard"""
    if 'user_id' not in session or session.get('user_role') != 'teacher':
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        db = get_db()

        # Get all quizzes that have PDF metadata
        quizzes = db.execute('''
                             SELECT q.id,
                                    q.title,
                                    q.created_at,
                                    q.course_id,
                                    c.title               as course_title,
                                    qp.filename,
                                    qp.uploaded_at,
                                    COUNT(DISTINCT qa.id) as student_attempts,
                                    AVG(qa.score)         as avg_score
                             FROM quizzes q
                                      INNER JOIN quiz_pdfs qp ON q.id = qp.quiz_id
                                      LEFT JOIN courses c ON q.course_id = c.id
                                      LEFT JOIN quiz_answers qa ON q.id = qa.quiz_id
                             WHERE q.user_id = ?
                             GROUP BY q.id, q.title, q.created_at, q.course_id, c.title, qp.filename, qp.uploaded_at
                             ORDER BY q.created_at DESC
                             ''', (session['user_id'],)).fetchall()

        db.close()

        quizzes_list = []
        for quiz in quizzes:
            quiz_dict = safe_dict(quiz)
            quiz_dict['avg_score'] = round(quiz_dict.get('avg_score') or 0, 1)
            quiz_dict['student_attempts'] = quiz_dict.get('student_attempts') or 0
            quizzes_list.append(quiz_dict)

        print(f"✅ Loaded {len(quizzes_list)} PDF quizzes for teacher")
        return jsonify({'success': True, 'quizzes': quizzes_list}), 200

    except Exception as e:
        print(f"❌ Get PDF quizzes error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e), 'quizzes': []}), 500


@app.route('/api/teacher/upload-pdf-quiz', methods=['POST'])
def upload_pdf_quiz():
    """Upload PDF and generate quiz using AI"""
    print(f"📤 PDF upload request received from user_id: {session.get('user_id')}, role: {session.get('user_role')}")

    if 'user_id' not in session or session.get('user_role') != 'teacher':
        print("❌ Unauthorized access attempt")
        return jsonify({'success': False, 'message': 'Nicht autorisiert'}), 401

    try:
        print(f"📋 Request files keys: {list(request.files.keys())}")
        print(f"📋 Request form keys: {list(request.form.keys())}")

        # Validate file upload
        if 'pdf_file' not in request.files:
            print("❌ No pdf_file in request.files")
            return jsonify(
                {'success': False, 'message': 'Keine PDF-Datei hochgeladen. Bitte wählen Sie eine Datei aus.'}), 400

        pdf_file = request.files['pdf_file']
        print(f"📄 PDF file received: {pdf_file.filename}, content_type: {pdf_file.content_type}")

        if pdf_file.filename == '' or not pdf_file.filename:
            print("❌ Empty filename")
            return jsonify({'success': False, 'message': 'Keine Datei ausgewählt'}), 400

        if not allowed_file(pdf_file.filename):
            return jsonify({'success': False, 'message': 'Nur PDF-Dateien sind erlaubt'}), 400

        # Check file size
        pdf_file.seek(0, os.SEEK_END)
        file_size = pdf_file.tell()
        pdf_file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify(
                {'success': False, 'message': f'Datei zu groß (max {MAX_FILE_SIZE // (1024 * 1024)}MB)'}), 400

        # Get form data
        title = request.form.get('title', '').strip()
        course_id = request.form.get('course_id')
        num_questions_str = request.form.get('num_questions', '10')
        difficulty = request.form.get('difficulty', 'medium')

        print(
            f"📝 Form data: title={title}, course_id={course_id}, num_questions={num_questions_str}, difficulty={difficulty}")

        try:
            num_questions = int(num_questions_str)
        except (ValueError, TypeError):
            num_questions = 10
            print(f"⚠️ Invalid num_questions, using default: 10")

        if not title or not course_id:
            print(f"❌ Missing required fields: title={bool(title)}, course_id={bool(course_id)}")
            return jsonify({'success': False, 'message': 'Titel und Kurs sind erforderlich'}), 400

        # Validate course exists
        db = get_db()
        course = db.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        if not course:
            db.close()
            return jsonify({'success': False, 'message': 'Kurs nicht gefunden'}), 404

        # Extract text from PDF
        print(f"📄 Extracting text from PDF: {pdf_file.filename}")
        pdf_text = extract_text_from_pdf(pdf_file)

        if not pdf_text or len(pdf_text.strip()) < 100:
            db.close()
            return jsonify(
                {'success': False, 'message': 'PDF enthält zu wenig Text oder konnte nicht gelesen werden'}), 400

        print(f"✅ Extracted {len(pdf_text)} characters from PDF")

        # Generate quiz using AI
        print(f"🤖 Generating quiz from PDF content...")
        generator = PDFQuizGenerator()
        quiz_data = generator.generate_quiz_from_pdf(
            pdf_text=pdf_text,
            num_questions=num_questions,
            difficulty=difficulty
        )

        if not quiz_data or 'questions' not in quiz_data:
            db.close()
            return jsonify({'success': False, 'message': 'Quiz-Generierung fehlgeschlagen'}), 500

        # Save quiz to database
        quiz_title = title
        questions_json = json.dumps(quiz_data, ensure_ascii=False)
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor = db.execute('''
                            INSERT INTO quizzes (course_id, user_id, title, questions_json, attempt_number, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ''', (course_id, session['user_id'], quiz_title, questions_json, 1, created_at))

        quiz_id = cursor.lastrowid

        # Save PDF metadata
        filename = secure_filename(pdf_file.filename)
        db.execute('''
                   INSERT INTO quiz_pdfs (quiz_id, filename, pdf_text, uploaded_by, uploaded_at)
                   VALUES (?, ?, ?, ?, ?)
                   ''', (quiz_id, filename, pdf_text[:10000], session['user_id'], created_at))

        db.commit()
        db.close()

        print(f"✅ PDF quiz created successfully: {quiz_title} (ID: {quiz_id})")
        return jsonify({
            'success': True,
            'message': f'Quiz "{quiz_title}" erfolgreich erstellt!',
            'quiz_id': quiz_id
        }), 201

    except Exception as e:
        print(f"❌ PDF upload error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Fehler: {str(e)}'}), 500

    # 1. Users table
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       name
                       TEXT
                       NOT
                       NULL,
                       email
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       password
                       TEXT
                       NOT
                       NULL,
                       role
                       TEXT
                       DEFAULT
                       'student',
                       points
                       INTEGER
                       DEFAULT
                       0,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    # 2. Profiles
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS profiles
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       UNIQUE
                       NOT
                       NULL,
                       avatar_url
                       TEXT,
                       birthdate
                       DATE,
                       country
                       TEXT,
                       bio
                       TEXT,
                       favorite_language
                       TEXT,
                       experience_level
                       TEXT
                       DEFAULT
                       'beginner',
                       profile_visible
                       BOOLEAN
                       DEFAULT
                       1,
                       friend_requests
                       BOOLEAN
                       DEFAULT
                       1,
                       email_notifications
                       BOOLEAN
                       DEFAULT
                       1,
                       updated_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 3. Courses
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS courses
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       category
                       TEXT,
                       color
                       TEXT,
                       total_lessons
                       INTEGER
                       DEFAULT
                       0,
                       duration
                       TEXT,
                       rating
                       REAL
                       DEFAULT
                       0,
                       status
                       TEXT
                       DEFAULT
                       'active'
                   )
                   ''')

    # 4. Enrollments
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS enrollments
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       course_id
                       INTEGER
                       NOT
                       NULL,
                       enrolled_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       UNIQUE
                   (
                       user_id,
                       course_id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE,
                       FOREIGN KEY
                   (
                       course_id
                   ) REFERENCES courses
                   (
                       id
                   )
                     ON DELETE CASCADE
                       )
                   ''')

    # 5. AI Tasks
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS ai_tasks
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       task_id
                       TEXT
                       UNIQUE
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       topic
                       TEXT,
                       difficulty
                       TEXT,
                       language
                       TEXT,
                       examples
                       TEXT,
                       hints
                       TEXT,
                       solution
                       TEXT,
                       test_cases
                       TEXT,
                       estimated_time
                       INTEGER,
                       points_reward
                       INTEGER
                       DEFAULT
                       1000,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       completed
                       BOOLEAN
                       DEFAULT
                       0,
                       completed_at
                       TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 6. AI Submissions
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS ai_submissions
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       task_id
                       TEXT
                       NOT
                       NULL,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       code
                       TEXT
                       NOT
                       NULL,
                       passed_tests
                       INTEGER
                       DEFAULT
                       0,
                       total_tests
                       INTEGER
                       DEFAULT
                       0,
                       points_earned
                       INTEGER
                       DEFAULT
                       0,
                       submitted_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 7. Friendships
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS friendships
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       friend_id
                       INTEGER
                       NOT
                       NULL,
                       status
                       TEXT
                       DEFAULT
                       'pending',
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       UNIQUE
                   (
                       user_id,
                       friend_id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE,
                       FOREIGN KEY
                   (
                       friend_id
                   ) REFERENCES users
                   (
                       id
                   )
                     ON DELETE CASCADE
                       )
                   ''')

    # 8. Points History
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS points_history
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       points
                       INTEGER
                       NOT
                       NULL,
                       reason
                       TEXT,
                       task_id
                       TEXT,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   ) ON DELETE CASCADE
                       )
                   ''')

    # 9. Quizzes
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS quizzes
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       course_id
                       INTEGER
                       NOT
                       NULL,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       title
                       TEXT
                       NOT
                       NULL,
                       questions_json
                       TEXT
                       NOT
                       NULL,
                       attempt_number
                       INTEGER
                       DEFAULT
                       1,
                       created_at
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       course_id
                   ) REFERENCES courses
                   (
                       id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # 10. Quiz answers
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS quiz_answers
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       quiz_id
                       INTEGER
                       NOT
                       NULL,
                       user_id
                       INTEGER
                       NOT
                       NULL,
                       answers_json
                       TEXT
                       NOT
                       NULL,
                       score
                       INTEGER
                       NOT
                       NULL,
                       passed
                       INTEGER
                       NOT
                       NULL,
                       feedback
                       TEXT,
                       submitted_at
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       quiz_id
                   ) REFERENCES quizzes
                   (
                       id
                   ),
                       FOREIGN KEY
                   (
                       user_id
                   ) REFERENCES users
                   (
                       id
                   )
                       )
                   ''')

    # 11. Quiz PDFs (NEW TABLE)
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS quiz_pdfs
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       quiz_id
                       INTEGER
                       NOT
                       NULL,
                       filename
                       TEXT
                       NOT
                       NULL,
                       pdf_text
                       TEXT,
                       uploaded_by
                       INTEGER
                       NOT
                       NULL,
                       uploaded_at
                       TEXT
                       NOT
                       NULL,
                       FOREIGN
                       KEY
                   (
                       quiz_id
                   ) REFERENCES quizzes
                   (
                       id
                   ) ON DELETE CASCADE,
                       FOREIGN KEY
                   (
                       uploaded_by
                   ) REFERENCES users
                   (
                       id
                   )
                     ON DELETE CASCADE
                       )
                   ''')

    # Create test teacher if doesn't exist
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "teacher"')
    teacher_count = cursor.fetchone()['count']

    if teacher_count == 0:
        print("👨‍🏫 Creating test teacher...")
        hashed = hash_password('teacher123')
        cursor.execute('INSERT INTO users (name, email, password, role, points) VALUES (?, ?, ?, ?, ?)',
                       ('Herr Schmidt', 'teacher@octocode.de', hashed, 'teacher', 0))
        teacher_id = cursor.lastrowid
        cursor.execute('INSERT INTO profiles (user_id) VALUES (?)', (teacher_id,))
        print("✅ Test teacher created: teacher@octocode.de / teacher123")

    # Create test courses if don't exist
    cursor.execute('SELECT COUNT(*) as count FROM courses')
    course_count = cursor.fetchone()['count']

    if course_count == 0:
        print("📚 Creating test courses...")
        test_courses = [
            ('Python Grundlagen', 'Lerne die Basics von Python', 'Programmierung', '#3b82f6', 12, '8 Wochen', 4.5,
             'active'),
            ('JavaScript für Anfänger', 'Webentwicklung mit JS', 'Web Development', '#f59e0b', 10, '6 Wochen', 4.3,
             'active'),
            ('HTML & CSS Basics', 'Erstelle deine erste Website', 'Web Design', '#10b981', 8, '4 Wochen', 4.7,
             'active'),
        ]
        for course in test_courses:
            cursor.execute('''
                           INSERT INTO courses (title, description, category, color, total_lessons, duration, rating,
                                                status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           ''', course)
        print(f"✅ {len(test_courses)} courses created")

    db.commit()
    db.close()
    print("✅ Database initialized")


if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("🚀 OctoCode Backend läuft auf http://127.0.0.1:5001")
    print("⚡ Groq AI aktiviert!")
    print("🎯 Points & Friends System aktiv!")
    print("👨‍🏫 Teacher Dashboard aktiv!")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)