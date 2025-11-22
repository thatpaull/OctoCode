#!/usr/bin/env python3
"""
OctoCode Database Migration Script
Führen Sie dieses Skript aus, um die Datenbank automatisch zu aktualisieren
"""

import sqlite3
import os

DATABASE = 'octocode.db'


def migrate_database():
	"""Migriert die Datenbank zu neuem Schema"""

	if not os.path.exists(DATABASE):
		print(f"❌ Datenbank {DATABASE} nicht gefunden!")
		print("Starten Sie zuerst app.py, um die Datenbank zu erstellen.")
		return False

	print(f"🔄 Starte Migration für {DATABASE}...")

	try:
		conn = sqlite3.connect(DATABASE)
		cursor = conn.cursor()

		# 1. Fügen Sie points Spalte hinzu
		print("1️⃣ Füge 'points' Spalte zur users Tabelle hinzu...")
		try:
			cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
			print("   ✅ Spalte 'points' hinzugefügt")
		except sqlite3.OperationalError as e:
			if "duplicate column" in str(e).lower():
				print("   ℹ️  Spalte 'points' existiert bereits")
			else:
				raise

		# 2. Aktualisieren Sie NULL-Werte
		cursor.execute("UPDATE users SET points = 0 WHERE points IS NULL")
		print("   ✅ Bestehende Benutzer aktualisiert")

		# 3. Erstellen Sie friendships Tabelle
		print("2️⃣ Erstelle 'friendships' Tabelle...")
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
		print("   ✅ Tabelle 'friendships' erstellt")

		# 4. Erstellen Sie points_history Tabelle
		print("3️⃣ Erstelle 'points_history' Tabelle...")
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
		print("   ✅ Tabelle 'points_history' erstellt")

		# 5. Fügen Sie Spalten zu ai_tasks hinzu
		print("4️⃣ Aktualisiere 'ai_tasks' Tabelle...")
		try:
			cursor.execute("ALTER TABLE ai_tasks ADD COLUMN points_reward INTEGER DEFAULT 1000")
			print("   ✅ Spalte 'points_reward' hinzugefügt")
		except sqlite3.OperationalError as e:
			if "duplicate column" in str(e).lower():
				print("   ℹ️  Spalte 'points_reward' existiert bereits")
			else:
				raise

		try:
			cursor.execute("ALTER TABLE ai_tasks ADD COLUMN completed_at TIMESTAMP")
			print("   ✅ Spalte 'completed_at' hinzugefügt")
		except sqlite3.OperationalError as e:
			if "duplicate column" in str(e).lower():
				print("   ℹ️  Spalte 'completed_at' existiert bereits")
			else:
				raise

		# 6. Aktualisieren Sie bestehende Tasks
		cursor.execute("UPDATE ai_tasks SET points_reward = 1000 WHERE points_reward IS NULL OR points_reward = 0")
		print("   ✅ Bestehende Tasks aktualisiert")

		# 7. Fügen Sie Spalte zu ai_submissions hinzu
		print("5️⃣ Aktualisiere 'ai_submissions' Tabelle...")
		try:
			cursor.execute("ALTER TABLE ai_submissions ADD COLUMN points_earned INTEGER DEFAULT 0")
			print("   ✅ Spalte 'points_earned' hinzugefügt")
		except sqlite3.OperationalError as e:
			if "duplicate column" in str(e).lower():
				print("   ℹ️  Spalte 'points_earned' existiert bereits")
			else:
				raise

		# Speichern Sie alle Änderungen
		conn.commit()

		# Verifizieren Sie die Tabellen
		print("\n📊 Verifiziere Tabellen...")

		tables = ['users', 'friendships', 'points_history', 'ai_tasks', 'ai_submissions']
		for table in tables:
			cursor.execute(f"PRAGMA table_info({table})")
			columns = cursor.fetchall()
			print(f"\n✅ Tabelle '{table}' ({len(columns)} Spalten):")
			for col in columns:
				print(f"   - {col[1]} ({col[2]})")

		conn.close()

		print("\n" + "=" * 50)
		print("✅ MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
		print("=" * 50)
		print("\n💡 Sie können jetzt app.py starten!")

		return True

	except Exception as e:
		print(f"\n❌ FEHLER bei der Migration: {e}")
		import traceback
		traceback.print_exc()
		return False


if __name__ == '__main__':
	print("=" * 50)
	print("🚀 OctoCode Database Migration Tool")
	print("=" * 50)
	print()

	migrate_database()
