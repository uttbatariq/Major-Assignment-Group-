import sqlite3
from werkzeug.security import generate_password_hash

DB = 'tourism.db'

schema = '''
CREATE TABLE IF NOT EXISTS admins (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tours (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  price REAL NOT NULL,
  duration INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS registrations (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  tour_id TEXT NOT NULL,
  registration_date TEXT NOT NULL,
  FOREIGN KEY(tour_id) REFERENCES tours(id),
  FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS tokens (
  id TEXT PRIMARY KEY,
  admin_id TEXT NOT NULL,
  token TEXT UNIQUE NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(admin_id) REFERENCES admins(id)
);
'''


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executescript(schema)
    # create default admin if not exists
    c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        import uuid
        admin_id = str(uuid.uuid4())
        pw = generate_password_hash('adminpass')
        c.execute('INSERT INTO admins (id, username, password) VALUES (?, ?, ?)', (admin_id, 'admin', pw))
        print('Default admin created: username=admin password=adminpass')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
    print('DB initialized at', DB)
