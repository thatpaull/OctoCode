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

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'your-secret-key-change-it-in-production'
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


def init_db():
	"""Инициализация базы данных"""
	print("🔄 Инициализация базы данных...")
	db = get_db()
	cursor = db.cursor()

	# 1. Создаем users таблицу
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

	# Создаем тестовых пользователей если их нет
	cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = "teacher"')
	teacher_count = cursor.fetchone()['count']

	if teacher_count == 0:
		print("📝 Создаем тестового учителя...")
		hashed = hash_password('teacher123')
		cursor.execute('INSERT INTO users (name, email, password, role, points) VALUES (?, ?, ?, ?, ?)',
					   ('Herr Schmidt', 'teacher@octocode.de', hashed, 'teacher', 0))
		teacher_id = cursor.lastrowid
		cursor.execute('INSERT INTO profiles (user_id) VALUES (?)', (teacher_id,))
		print("✅ Тестовый учитель создан: teacher@octocode.de / teacher123")

	# Создаем тестовые курсы если их нет
	cursor.execute('SELECT COUNT(*) as count FROM courses')
	course_count = cursor.fetchone()['count']

	if course_count == 0:
		print("📚 Создаем тестовые курсы...")
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
		print(f"✅ {len(test_courses)} Kurse erstellt")
		
# Quizzes table
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS quizzes (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			course_id INTEGER NOT NULL,
			user_id INTEGER NOT NULL,
			title TEXT NOT NULL,
			questions_json TEXT NOT NULL,
			created_at TEXT NOT NULL,
			FOREIGN KEY (course_id) REFERENCES courses(id),
			FOREIGN KEY (user_id) REFERENCES users(id)
		)
	''')
	
	# Quiz answers table
	cursor.execute('''
		CREATE TABLE IF NOT EXISTS quiz_answers (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			quiz_id INTEGER NOT NULL,
			user_id INTEGER NOT NULL,
			answers_json TEXT NOT NULL,
			score INTEGER NOT NULL,
			passed INTEGER NOT NULL,
			submitted_at TEXT NOT NULL,
			FOREIGN KEY (quiz_id) REFERENCES quizzes(id),
			FOREIGN KEY (user_id) REFERENCES users(id)
		)
	''')
	db.commit()
	db.close()
	print("✅ База данных инициализирована")


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
			WHERE u.id IN (
				SELECT friend_id FROM friendships
				WHERE user_id = ? AND status = "accepted"
				UNION
				SELECT user_id FROM friendships
				WHERE friend_id = ? AND status = "accepted"
			)
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
		return jsonify([safe_dict(c) for c in courses]), 200
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
        
        # Create lessons based on course title
        if 'Python' in course_dict.get('title', ''):
            # Python für Anfänger: 12 Lektionen, 6h total (30min each)
            lessons = [
                {
                    'id': 1,
                    'title': 'Einführung in Python',
                    'duration': 30,
                    'completed': False,
                    'content': 'Willkommen bei Python! In dieser Lektion lernst du was Python ist und wie du es installierst.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=0&end=1800'
                },
                {
                    'id': 2,
                    'title': 'Variablen und Datentypen',
                    'duration': 30,
                    'completed': False,
                    'content': 'Lerne wie man Variablen erstellt und die verschiedenen Datentypen in Python kennt.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=1800&end=3600'
                },
                {
                    'id': 3,
                    'title': 'Strings und Textverarbeitung',
                    'duration': 30,
                    'completed': False,
                    'content': 'Arbeite mit Text: String-Methoden, Formatting und mehr.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=3600&end=5400'
                },
                {
                    'id': 4,
                    'title': 'Listen und Tuples',
                    'duration': 30,
                    'completed': False,
                    'content': 'Entdecke Listen und Tuples - wichtige Datenstrukturen in Python.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=5400&end=7200'
                },
                {
                    'id': 5,
                    'title': 'Dictionaries und Sets',
                    'duration': 30,
                    'completed': False,
                    'content': 'Lerne Dictionaries für Key-Value Paare und Sets kennen.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=7200&end=9000'
                },
                {
                    'id': 6,
                    'title': 'If-Else Bedingungen',
                    'duration': 30,
                    'completed': False,
                    'content': 'Treffe Entscheidungen in deinem Code mit if-else Statements.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=9000&end=10800'
                },
                {
                    'id': 7,
                    'title': 'For Schleifen',
                    'duration': 30,
                    'completed': False,
                    'content': 'Wiederhole Code effizient mit for-Loops.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=10800&end=12600'
                },
                {
                    'id': 8,
                    'title': 'While Schleifen',
                    'duration': 30,
                    'completed': False,
                    'content': 'Lerne while-Loops für bedingte Wiederholungen.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=12600&end=14400'
                },
                {
                    'id': 9,
                    'title': 'Funktionen',
                    'duration': 30,
                    'completed': False,
                    'content': 'Erstelle wiederverwendbare Funktionen.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=14400&end=16200'
                },
                {
                    'id': 10,
                    'title': 'Module und Imports',
                    'duration': 30,
                    'completed': False,
                    'content': 'Arbeite mit Python-Modulen und externen Bibliotheken.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=16200&end=18000'
                },
                {
                    'id': 11,
                    'title': 'Fehlerbehandlung',
                    'duration': 30,
                    'completed': False,
                    'content': 'Behandle Fehler professionell mit try-except.',
                    'video_url': 'https://www.youtube.com/embed/e6vPt_e9sRw?start=18000&end=19800'
                },
                {
                    'id': 12,
                    'title': 'Praxis-Projekt',
                    'duration': 30,
                    'completed': False,
                    'content': 'Wende dein Wissen an: Erstelle dein erstes Python-Projekt!',
                    'video_url': 'https://www.youtube.com/embed/kqtD5dpn9C8'
                }
            ]
        elif 'HTML' in course_dict.get('title', '') or 'CSS' in course_dict.get('title', '') or 'Web' in course_dict.get('title', ''):
            # Webentwicklung mit HTML/CSS: 8 Lektionen, 4h total (30min average)
            lessons = [
                {
                    'id': 1,
                    'title': 'HTML Grundlagen - Einführung',
                    'duration': 20,
                    'completed': False,
                    'content': 'Lerne HTML in 20 Minuten! Was ist HTML? Grundstruktur, Elemente und Tags.',
                    'video_url': 'https://www.youtube.com/embed/Q3MIitoSQkE'
                },
                {
                    'id': 2,
                    'title': 'HTML Vertiefung',
                    'duration': 35,
                    'completed': False,
                    'content': 'Vertiefe dein HTML-Wissen: Formulare, Tabellen und semantische Elemente.',
                    'video_url': 'https://www.youtube.com/embed/Q3MIitoSQkE'
                },
                {
                    'id': 3,
                    'title': 'HTML Praxis',
                    'duration': 25,
                    'completed': False,
                    'content': 'Praktische HTML-Übungen: Erstelle deine erste Webseite.',
                    'video_url': 'https://www.youtube.com/embed/Q3MIitoSQkE'
                },
                {
                    'id': 4,
                    'title': 'CSS Grundlagen - Teil 1',
                    'duration': 30,
                    'completed': False,
                    'content': 'CSS Kurs in 40 Minuten! Einführung: Selektoren, Farben und Text.',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=0&end=1200'
                },
                {
                    'id': 5,
                    'title': 'CSS Grundlagen - Teil 2',
                    'duration': 30,
                    'completed': False,
                    'content': 'Box Model: margin, padding, border verstehen und anwenden.',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=600&end=1800'
                },
                {
                    'id': 6,
                    'title': 'CSS Layout - Flexbox',
                    'duration': 30,
                    'completed': False,
                    'content': 'Moderne Layouts mit Flexbox erstellen.',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=1200&end=2400'
                },
                {
                    'id': 7,
                    'title': 'CSS Positionierung',
                    'duration': 30,
                    'completed': False,
                    'content': 'Elemente positionieren: relative, absolute, fixed.',
                    'video_url': 'https://www.youtube.com/embed/I84aQhbJl_Y?start=1800&end=3000'
                },
                {
                    'id': 8,
                    'title': 'CSS & HTML Projekt',
                    'duration': 40,
                    'completed': False,
                    'content': 'Abschlussprojekt: Erstelle eine komplette responsive Webseite!',
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
		return jsonify([safe_dict(r) for r in rows]), 200
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

class QuizGenerator:
	def __init__(self, course_title, course_description):
		self.course_title = course_title
		self.course_description = course_description
	
def generate_quiz(self, num_questions=10, user_id=None, difficulty="medium"):
	"""Generate quiz using Groq AI with randomization and difficulty"""
	try:
		# Add randomization seed based on timestamp and user_id
		import time
		seed = int(time.time() * 1000) + (user_id or 0)
		
		# Difficulty descriptions for AI
		difficulty_map = {
			"easy": "einfach - Grundlegende Konzepte, direkte Fragen",
			"medium": "mittel - Anwendung von Konzepten, einige Denkaufgaben",
			"hard": "schwer - Komplexe Probleme, fortgeschrittene Konzepte",
			"adaptive": "gemischt - Verschiedene Schwierigkeitsgrade"
		}
		
		difficulty_desc = difficulty_map.get(difficulty, difficulty_map["medium"])
		
		prompt = f"""Du bist ein Experte für Bildungsinhalte. Erstelle ein EINZIGARTIGES Quiz mit {num_questions} Fragen zum Thema: "{self.course_title}".

Kurs-Beschreibung: {self.course_description}

Schwierigkeitsgrad: {difficulty_desc}
Randomization Seed: {seed}

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

WICHTIG:
- Erstelle genau {num_questions} VERSCHIEDENE Fragen
- Passe die Schwierigkeit an: {difficulty_desc}
- 60% Multiple-Choice Fragen (type: "multiple_choice")
- 40% Code-Übungen (type: "code")
- Jede Frage sollte ein "difficulty" Feld haben: "easy", "medium", oder "hard"
- Für Code-Fragen: füge ein "code" Feld mit dem Code-Beispiel hinzu
- Nutze den Seed {seed} um UNTERSCHIEDLICHE Fragen zu generieren
- KEINE sich wiederholenden Fragen
- Explanationen sollen lehrreich und detailliert sein
- Alle Texte auf Deutsch
- NUR JSON zurückgeben, keine zusätzlichen Texte
"""

		response = groq_client.chat.completions.create(
			model="llama-3.3-70b-versatile",
			messages=[
				{
					"role": "system",
					"content": "Du bist ein professioneller Quiz-Generator. Generiere IMMER unterschiedliche Fragen. Antworte NUR mit validem JSON."
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
		
		# Remove markdown code blocks if present
		if response_text.startswith('```json'):
			response_text = response_text[7:]
		if response_text.startswith('```'):
			response_text = response_text[3:]
		if response_text.endswith('```'):
			response_text = response_text[:-3]
		response_text = response_text.strip()

		quiz_data = json.loads(response_text)
		
		# Add unique IDs and ensure difficulty field exists
		for i, question in enumerate(quiz_data['questions']):
			question['id'] = i + 1
			if 'difficulty' not in question:
				question['difficulty'] = difficulty
		
		return quiz_data

	except Exception as e:
		print(f"❌ Quiz generation error: {e}")
		import traceback
		traceback.print_exc()
		return self._get_fallback_quiz()

@app.route('/api/quizzes/<quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
	"""Get or generate a NEW quiz for a course"""
	if 'user_id' not in session:
		return jsonify({'success': False, 'message': 'Not authenticated'}), 401
	
	try:
		print(f"🎓 Quiz request received: {quiz_id}")
		
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
				SELECT qa.score FROM quiz_answers qa
				JOIN quizzes q ON qa.quiz_id = q.id
				WHERE q.course_id = ? AND q.user_id = ?
				ORDER BY qa.submitted_at DESC
				LIMIT 1
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
			SELECT COUNT(*) as count FROM quizzes 
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
		
		# Extract course_id
		course_id = int(quiz_id.replace('quiz_', ''))
		
		db = get_db()
		
		# Get quiz
		quiz = db.execute('''
			SELECT * FROM quizzes 
			WHERE course_id = ? AND user_id = ?
		''', (course_id, session['user_id'])).fetchone()
		
		if not quiz:
			db.close()
			return jsonify({'success': False, 'message': 'Quiz not found'}), 404
		
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
		
		# Save result to database
		db.execute('''
			INSERT INTO quiz_answers (quiz_id, user_id, answers_json, score, passed, submitted_at)
			VALUES (?, ?, ?, ?, ?, datetime('now'))
		''', (
			quiz['id'],
			session['user_id'],
			json.dumps(user_answers),
			score,
			1 if passed else 0
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
			'results': results
		}), 200
		
	except Exception as e:
		print(f"❌ Submit quiz error: {e}")
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


if __name__ == '__main__':
	init_db()
	print("=" * 60)
	print("🚀 OctoCode Backend läuft auf http://127.0.0.1:5001")
	print("⚡ Groq AI aktiviert!")
	print("🎯 Points & Friends System aktiv!")
	print("👨‍🏫 Teacher Dashboard aktiv!")
	print("=" * 60)
	app.run(debug=True, host='0.0.0.0', port=5001)
