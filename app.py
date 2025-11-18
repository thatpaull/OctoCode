from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import hashlib
import secrets
import base64
import json
from groq import Groq

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'your-secret-key-change-it'
CORS(app, supports_credentials=True, origins=['http://127.0.0.1:5001'])

DATABASE = 'octocode.db'
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GROQ_API_KEY = "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"
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


def init_db():
	with app.app_context():
		db = get_db()
		db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
		db.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                avatar_url TEXT,
                birthdate DATE,
                country TEXT,
                bio TEXT,
                favorite_language TEXT,
                experience_level TEXT DEFAULT 'beginner',
                profile_visible BOOLEAN DEFAULT 1,
                friend_requests BOOLEAN DEFAULT 1,
                email_notifications BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
		db.commit()
		db.close()
		print("✅ DB initialized / verified")


def init_courses_db():
	with app.app_context():
		db = get_db()
		db.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                color TEXT,
                total_lessons INTEGER DEFAULT 0,
                duration TEXT,
                rating REAL DEFAULT 0
            )
        ''')
		db.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, course_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
            )
        ''')
		db.commit()
		db.close()


def init_ai_tasks_db():
	with app.app_context():
		db = get_db()
		db.execute('''
            CREATE TABLE IF NOT EXISTS ai_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                topic TEXT,
                difficulty TEXT,
                language TEXT,
                examples TEXT,
                hints TEXT,
                solution TEXT,
                test_cases TEXT,
                estimated_time INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
		db.execute('''
            CREATE TABLE IF NOT EXISTS ai_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                passed_tests INTEGER DEFAULT 0,
                total_tests INTEGER DEFAULT 0,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
		db.commit()
		db.close()
		print("✅ AI Tasks DB initialized")


class TaskGenerator:
	def __init__(self):
		self.client = groq_client

	def generate_task(self, topic: str, user_id: int, difficulty: str = "Mittel", language: str = "Python"):
		seed = hashlib.md5(f"{user_id}_{topic}_{secrets.token_hex(4)}".encode()).hexdigest()[:8]

		prompt = f"""Du bist ein erfahrener Programmierlehrer. Erstelle eine einzigartige Programmieraufgabe auf Deutsch.

Parameter:
- Thema: {topic}
- Programmiersprache: {language}
- Schwierigkeitsgrad: {difficulty}
- Aufgaben-Code: {seed}

Anforderungen:
1. Die Aufgabe soll praktisch und interessant für Kinder/Jugendliche sein
2. Klare Beschreibung der Aufgabe
3. Mindestens 3 Beispiele mit Ein- und Ausgabe
4. Hilfreiche Tipps zum Lösen
5. Musterlösung mit Kommentaren
6. Testfälle zur Überprüfung

Antworte NUR mit JSON in diesem Format:
{{
  "title": "Titel der Aufgabe",
  "description": "Detaillierte Beschreibung (2-3 Sätze)",
  "difficulty": "{difficulty}",
  "topic": "{topic}",
  "examples": [
    {{"input": "Beispiel-Eingabe", "output": "Beispiel-Ausgabe", "explanation": "Erklärung"}},
    {{"input": "Eingabe 2", "output": "Ausgabe 2", "explanation": "Erklärung"}}
  ],
  "hints": ["Tipp 1", "Tipp 2", "Tipp 3"],
  "solution": "# Musterlösung mit Kommentaren\\ncode hier",
  "test_cases": [
    {{"input": "Test 1", "expected_output": "Erwartete Ausgabe"}},
    {{"input": "Test 2", "expected_output": "Erwartete Ausgabe"}}
  ],
  "estimated_time": 30
}}

Antworte NUR mit JSON, ohne zusätzlichen Text!"""

		try:
			completion = self.client.chat.completions.create(
				model="llama-3.3-70b-versatile",
				messages=[
					{
						"role": "system",
						"content": "Du bist ein hilfreicher Programmierlehrer. Antworte immer nur mit gültigem JSON."
					},
					{
						"role": "user",
						"content": prompt
					}
				],
				temperature=0.7,
				max_tokens=2000,
				top_p=1
			)

			text = completion.choices[0].message.content.strip()

			if text.startswith("```json"):
				text = text[7:]
			if text.startswith("```"):
				text = text[3:]
			if text.endswith("```"):
				text = text[:-3]

			task_data = json.loads(text.strip())
			task_data["task_id"] = seed
			task_data["language"] = language

			return task_data

		except Exception as e:
			print(f"❌ AI Error: {e}")
			import traceback
			traceback.print_exc()
			return None


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
			return jsonify({'success': False, 'message': 'Das Passwort muss mindestens 6 Zeichen lang sein!'}), 400

		db = get_db()
		existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
		if existing:
			db.close()
			return jsonify({'success': False, 'message': 'Diese E-Mail ist bereits registriert!'}), 400

		hashed = hash_password(password)
		cursor = db.execute('INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
							(name, email, hashed, role))
		user_id = cursor.lastrowid
		db.execute('INSERT INTO profiles (user_id) VALUES (?)', (user_id,))
		db.commit()
		db.close()

		return jsonify({'success': True, 'message': 'Registrierung erfolgreich! Sie können sich jetzt anmelden.'}), 201

	except Exception:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Bei der Registrierung ist ein Fehler aufgetreten.'}), 500


@app.route('/api/login', methods=['POST'])
def login():
	try:
		data = request.get_json() or {}
		email = (data.get('email') or '').strip().lower()
		password = (data.get('password') or '').strip()
		if not email or not password:
			return jsonify({'success': False, 'message': 'Bitte E-Mail und Passwort eingeben!'}), 400

		db = get_db()
		user = db.execute('SELECT * FROM users WHERE email = ? AND role = ?', (email, 'student')).fetchone()
		db.close()
		if not user or not verify_password(password, user['password']):
			return jsonify({'success': False, 'message': 'Falsche E-Mail oder Passwort!'}), 401

		session['user_id'] = user['id']
		session['user_name'] = user['name']
		session['user_email'] = user['email']
		session['user_role'] = user['role']

		return jsonify({
			'success': True,
			'message': f'Willkommen, {user["name"]}!',
			'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']},
			'redirect': '/dashboard.html'
		}), 200

	except Exception:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler bei der Anmeldung'}), 500


@app.route('/api/teacher-login', methods=['POST'])
def teacher_login():
	try:
		data = request.get_json() or {}
		email = (data.get('email') or '').strip().lower()
		password = (data.get('password') or '').strip()
		if not email or not password:
			return jsonify({'success': False, 'message': 'Bitte E-Mail und Passwort eingeben!'}), 400

		db = get_db()
		user = db.execute('SELECT * FROM users WHERE email = ? AND role = ?', (email, 'teacher')).fetchone()
		db.close()
		if not user or not verify_password(password, user['password']):
			return jsonify({'success': False, 'message': 'Falsche E-Mail oder Passwort oder kein Lehrer-Account!'}), 401

		session['user_id'] = user['id']
		session['user_name'] = user['name']
		session['user_email'] = user['email']
		session['user_role'] = user['role']

		return jsonify({
			'success': True,
			'message': f'Willkommen, {user["name"]}!',
			'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']},
			'redirect': '/teacher-admin.html'
		}), 200

	except Exception:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler bei der Anmeldung'}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
	session.clear()
	return jsonify({'success': True, 'message': 'Sie wurden erfolgreich abgemeldet!'}), 200


@app.route('/api/check-auth')
def check_auth():
	if 'user_id' not in session:
		return jsonify({'authenticated': False}), 200

	try:
		db = get_db()
		profile = db.execute('SELECT avatar_url FROM profiles WHERE user_id = ?', (session['user_id'],)).fetchone()

		avatar_url = None
		if profile and profile['avatar_url']:
			avatar_url = profile['avatar_url']
		else:
			avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={secrets.token_hex(8)}"
			try:
				db.execute('UPDATE profiles SET avatar_url = ? WHERE user_id = ?', (avatar_url, session['user_id']))
				db.commit()
			except Exception:
				import traceback
				traceback.print_exc()
		db.close()

		return jsonify({
			'authenticated': True,
			'user': {
				'id': session['user_id'],
				'name': session.get('user_name', ''),
				'email': session.get('user_email', ''),
				'role': session.get('user_role', 'student'),
				'avatar_url': avatar_url
			}
		}), 200

	except Exception:
		import traceback
		traceback.print_exc()
		return jsonify({'authenticated': False}), 200


@app.route('/api/teacher/students', methods=['GET'])
def get_teacher_students():
	if 'user_id' not in session or session.get('user_role') != 'teacher':
		return jsonify({'success': False, 'message': 'Unauthorized'}), 401

	try:
		db = get_db()
		students = db.execute('''
			SELECT u.id, u.name, u.email, u.created_at, p.avatar_url,
			       COALESCE((SELECT COUNT(*) FROM enrollments WHERE user_id = u.id), 0) as activeCourses,
			       0 as points, 0 as coursesCompleted, 0 as progress
			FROM users u
			LEFT JOIN profiles p ON u.id = p.user_id
			WHERE u.role = 'student'
			ORDER BY u.created_at DESC
		''').fetchall()
		db.close()

		students_list = [dict(student) for student in students]
		return jsonify(students_list), 200
	except Exception as e:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/teacher/tasks', methods=['GET'])
def get_teacher_tasks():
	if 'user_id' not in session or session.get('user_role') != 'teacher':
		return jsonify({'success': False, 'message': 'Unauthorized'}), 401

	try:
		db = get_db()
		tasks = db.execute('''
			SELECT t.id, t.task_id, t.title, t.topic, t.difficulty, t.language, t.estimated_time,
			       COUNT(DISTINCT s.id) as submissions,
			       SUM(CASE WHEN t.completed = 1 THEN 1 ELSE 0 END) as completed
			FROM ai_tasks t
			LEFT JOIN ai_submissions s ON t.task_id = s.task_id
			GROUP BY t.id
			ORDER BY t.created_at DESC
		''').fetchall()
		db.close()

		tasks_list = [dict(task) for task in tasks]
		return jsonify(tasks_list), 200
	except Exception as e:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/profile', methods=['GET'])
def get_profile():
	if 'user_id' not in session:
		return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401
	try:
		db = get_db()
		profile = db.execute('''
            SELECT p.*, u.name
            FROM profiles p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
        ''', (session['user_id'],)).fetchone()

		if not profile:
			db.close()
			return jsonify({'success': False, 'message': 'Profil nicht gefunden'}), 404

		avatar_url = profile['avatar_url']
		if not avatar_url:
			avatar_url = f"https://api.dicebear.com/7.x/avataaars/svg?seed={secrets.token_hex(8)}"
			try:
				db.execute('UPDATE profiles SET avatar_url = ? WHERE user_id = ?', (avatar_url, session['user_id']))
				db.commit()
			except Exception:
				import traceback
				traceback.print_exc()

		result = {
			'success': True,
			'avatar_url': avatar_url,
			'birthdate': profile['birthdate'] or '',
			'country': profile['country'] or '',
			'bio': profile['bio'] or '',
			'favorite_language': profile['favorite_language'] or '',
			'experience_level': profile['experience_level'] or 'beginner',
			'profile_visible': bool(profile['profile_visible']),
			'friend_requests': bool(profile['friend_requests']),
			'email_notifications': bool(profile['email_notifications'])
		}
		db.close()
		return jsonify(result), 200

	except Exception:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler beim Abrufen des Profils'}), 500


@app.route('/api/profile', methods=['PUT'])
def update_profile():
	if 'user_id' not in session:
		return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401
	try:
		data = request.get_json() or {}
		name = (data.get('name') or '').strip()
		avatar_url = data.get('avatar_url') or ''
		birthdate = data.get('birthdate') or None
		country = data.get('country') or None
		bio = (data.get('bio') or '').strip()
		favorite_language = data.get('favorite_language') or None
		experience_level = data.get('experience_level') or 'beginner'

		if not name:
			return jsonify({'success': False, 'message': 'Name ist erforderlich'}), 400
		if bio and len(bio) > 500:
			return jsonify({'success': False, 'message': 'Bio darf maximal 500 Zeichen lang sein'}), 400

		db = get_db()
		db.execute('UPDATE users SET name = ? WHERE id = ?', (name, session['user_id']))

		final_avatar_url = avatar_url
		if isinstance(avatar_url, str) and avatar_url.startswith('data:image'):
			try:
				header, encoded = avatar_url.split(',', 1)
				image_data = base64.b64decode(encoded)
				ext = 'jpg'
				if 'png' in header:
					ext = 'png'
				elif 'gif' in header:
					ext = 'gif'
				filename = f"avatar_{session['user_id']}_{secrets.token_hex(8)}.{ext}"
				filepath = os.path.join(UPLOAD_FOLDER, filename)
				with open(filepath, 'wb') as f:
					f.write(image_data)
				final_avatar_url = f'/uploads/{filename}'
			except Exception:
				import traceback
				traceback.print_exc()

		db.execute('''
            UPDATE profiles
            SET avatar_url = ?, birthdate = ?, country = ?, bio = ?, favorite_language = ?, experience_level = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (final_avatar_url, birthdate, country, bio, favorite_language, experience_level, session['user_id']))
		db.commit()
		db.close()

		session['user_name'] = name

		return jsonify(
			{'success': True, 'message': 'Profil erfolgreich aktualisiert!', 'avatar_url': final_avatar_url}), 200

	except Exception:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler beim Aktualisieren des Profils'}), 500


@app.route('/api/privacy', methods=['PUT'])
def update_privacy():
	if 'user_id' not in session:
		return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401
	try:
		data = request.get_json() or {}
		profile_visible = bool(data.get('profile_visible', True))
		friend_requests = bool(data.get('friend_requests', True))
		email_notifications = bool(data.get('email_notifications', True))

		db = get_db()
		db.execute('''
            UPDATE profiles
            SET profile_visible = ?, friend_requests = ?, email_notifications = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (profile_visible, friend_requests, email_notifications, session['user_id']))
		db.commit()
		db.close()
		return jsonify({'success': True, 'message': 'Datenschutzeinstellungen aktualisiert!'}), 200
	except Exception:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler beim Aktualisieren der Datenschutzeinstellungen'}), 500


@app.route('/api/courses', methods=['GET'])
def get_courses():
	db = get_db()
	courses = db.execute('SELECT * FROM courses').fetchall()
	db.close()
	courses_list = [dict(course) for course in courses]
	return jsonify(courses_list)


@app.route('/api/my-courses', methods=['GET'])
def get_my_courses():
	if 'user_id' not in session:
		return jsonify([]), 200
	db = get_db()
	rows = db.execute('''
        SELECT c.*
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        WHERE e.user_id = ?
    ''', (session['user_id'],)).fetchall()
	db.close()
	courses_list = [dict(r) for r in rows]
	return jsonify(courses_list)


@app.route('/api/enroll', methods=['POST'])
def enroll_course():
	if 'user_id' not in session:
		return jsonify({'success': False, 'message': 'Nicht angemeldet'}), 401

	data = request.get_json() or {}
	course_id = data.get('course_id')
	if not course_id:
		return jsonify({'success': False, 'message': 'Kein Kurs ausgewählt'}), 400

	db = get_db()
	try:
		db.execute('INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?, ?)',
				   (session['user_id'], course_id))
		db.commit()
		db.close()
		return jsonify({'success': True, 'message': 'Kurs erfolgreich angemeldet!'})
	except Exception as e:
		db.close()
		return jsonify({'success': False, 'message': 'Fehler beim Anmelden zum Kurs'}), 500


@app.route('/api/ai/generate-task', methods=['POST'])
def ai_generate_task():
	if 'user_id' not in session:
		return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

	try:
		data = request.get_json() or {}
		topic = data.get('topic', 'Python Grundlagen')
		difficulty = data.get('difficulty', 'Mittel')
		language = data.get('language', 'Python')

		generator = TaskGenerator()
		task_data = generator.generate_task(topic, session['user_id'], difficulty, language)

		if not task_data:
			return jsonify({'success': False, 'message': 'Fehler bei der Aufgabengenerierung'}), 500

		db = get_db()
		db.execute('''
            INSERT INTO ai_tasks (user_id, task_id, title, description, topic, difficulty, language,
                                  examples, hints, solution, test_cases, estimated_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
			session['user_id'],
			task_data['task_id'],
			task_data['title'],
			task_data['description'],
			task_data['topic'],
			task_data['difficulty'],
			task_data['language'],
			json.dumps(task_data['examples']),
			json.dumps(task_data['hints']),
			task_data['solution'],
			json.dumps(task_data['test_cases']),
			task_data.get('estimated_time', 30)
		))
		db.commit()
		db.close()

		return jsonify({'success': True, 'task': task_data}), 200

	except Exception as e:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler bei der AI-Generierung'}), 500


@app.route('/api/ai/my-tasks', methods=['GET'])
def ai_get_my_tasks():
	if 'user_id' not in session:
		return jsonify([]), 200

	try:
		db = get_db()
		tasks = db.execute('''
            SELECT id, task_id, title, description, topic, difficulty, language,
                   estimated_time, created_at, completed
            FROM ai_tasks
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (session['user_id'],)).fetchall()
		db.close()

		tasks_list = [dict(task) for task in tasks]
		return jsonify(tasks_list), 200

	except Exception as e:
		import traceback
		traceback.print_exc()
		return jsonify([]), 200


@app.route('/api/ai/task/<task_id>', methods=['GET'])
def ai_get_task(task_id):
	if 'user_id' not in session:
		return jsonify({'success': False, 'message': 'Nicht authentifiziert'}), 401

	try:
		db = get_db()
		task = db.execute('''
            SELECT * FROM ai_tasks
            WHERE task_id = ? AND user_id = ?
        ''', (task_id, session['user_id'])).fetchone()
		db.close()

		if not task:
			return jsonify({'success': False, 'message': 'Aufgabe nicht gefunden'}), 404

		task_data = dict(task)
		task_data['examples'] = json.loads(task_data['examples'])
		task_data['hints'] = json.loads(task_data['hints'])
		task_data['test_cases'] = json.loads(task_data['test_cases'])

		return jsonify({'success': True, 'task': task_data}), 200

	except Exception as e:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler beim Laden der Aufgabe'}), 500


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
		db.execute('''
            INSERT INTO ai_submissions (task_id, user_id, code)
            VALUES (?, ?, ?)
        ''', (task_id, session['user_id'], code))

		db.execute('''
            UPDATE ai_tasks
            SET completed = 1
            WHERE task_id = ? AND user_id = ?
        ''', (task_id, session['user_id']))

		db.commit()
		db.close()

		return jsonify({'success': True, 'message': 'Lösung erfolgreich eingereicht!'}), 200

	except Exception as e:
		import traceback
		traceback.print_exc()
		return jsonify({'success': False, 'message': 'Fehler beim Einreichen'}), 500


if __name__ == '__main__':
	init_db()
	init_courses_db()
	init_ai_tasks_db()
	print("🚀 OctoCode Backend mit Groq AI läuft auf http://127.0.0.1:5001")
	print("⚡ Groq Llama-3.3-70B aktiviert!")
	print("👨‍🏫 Teacher Admin Panel verfügbar!")
	app.run(debug=True, host='0.0.0.0', port=5001)
