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
	# Убедимся что points всегда число
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
					   0
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

			# Entferne Code-Blöcke
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
			f"https://api.dicebear.com/7.x/avataaars/svg?seed={secrets.token_hex(8)}"

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

		# Speichere Lösung
		db.execute('INSERT INTO ai_submissions (task_id, user_id, code, points_earned) VALUES (?, ?, ?, ?)',
				   (task_id, session['user_id'], code, points_earned))

		# Markiere als abgeschlossen
		db.execute(
			'UPDATE ai_tasks SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE task_id = ? AND user_id = ?',
			(task_id, session['user_id']))

		# Füge Punkte hinzu
		db.execute('UPDATE users SET points = points + ? WHERE id = ?',
				   (points_earned, session['user_id']))

		# History
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


# ============ OTHER ENDPOINTS ============

@app.route('/api/courses', methods=['GET'])
def get_courses():
	db = get_db()
	courses = db.execute('SELECT * FROM courses').fetchall()
	db.close()
	return jsonify([dict(c) for c in courses])


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
	return jsonify([dict(r) for r in rows])

@app.route('/api/enroll', methods=['POST'])
def enroll_course():
    if 'user_id' not in session:
        return jsonify({"success": False, "message": "Nicht authentifiziert"}), 401

    data = request.get_json() or {}
    course_id = data.get('course_id')

    if not course_id:
        return jsonify({"success": False, "message": "Kurs-ID fehlt"}), 400

    db = get_db()

    # prüfen ob user schon eingeschrieben ist
    existing = db.execute(
        "SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?",
        (session['user_id'], course_id)
    ).fetchone()

    if existing:
        db.close()
        return jsonify({"success": False, "message": "Bereits eingeschrieben"}), 400

    # speichern
    db.execute(
        "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
        (session['user_id'], course_id)
    )
    db.commit()
    db.close()

    return jsonify({"success": True, "message": "Erfolgreich eingeschrieben"}), 200

if __name__ == '__main__':
	init_db()
	print("=" * 60)
	print("🚀 OctoCode Backend läuft auf http://127.0.0.1:5001")
	print("⚡ Groq AI aktiviert!")
	print("🎯 Points & Friends System aktiv!")
	print("=" * 60)
	app.run(debug=True, host='0.0.0.0', port=5001)
