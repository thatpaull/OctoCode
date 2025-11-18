import hashlib
import secrets

def hash_password(password):
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"

# Generate hash for teacher123
password = "teacher123"
hashed = hash_password(password)

print("=" * 60)
print("COPY THIS HASH:")
print("=" * 60)
print(hashed)
print("=" * 60)
print("\nSQL Command:")
print("=" * 60)
print(f"""
DELETE FROM users WHERE email = 'teacher@octocode.at';

INSERT INTO users (name, email, password, role)
VALUES (
    'Teacher Name',
    'teacher@octocode.at',
    '{hashed}',
    'teacher'
);

INSERT INTO profiles (user_id, avatar_url)
VALUES (
    (SELECT id FROM users WHERE email = 'teacher@octocode.at'),
    'https://api.dicebear.com/7.x/avataaars/svg?seed=teacher'
);
""")
print("=" * 60)
print("\nLogin with:")
print("Email: teacher@octocode.at")
print("Password: teacher123")
print("=" * 60)
