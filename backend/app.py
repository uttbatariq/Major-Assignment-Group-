from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

DB = 'tourism.db'

app = Flask(__name__)
CORS(app)

# --- DB helpers ---

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, args)
    conn.commit()
    return cur.lastrowid

# --- Auth ---

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error':'username/password required'}), 400
    row = query('SELECT * FROM admins WHERE username = ?', (username,), one=True)
    if not row:
        return jsonify({'error':'invalid credentials'}), 401
    if not check_password_hash(row['password'], password):
        return jsonify({'error':'invalid credentials'}), 401
    token = str(uuid.uuid4())
    import datetime
    execute('INSERT INTO tokens (id, admin_id, token, created_at) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), row['id'], token, str(datetime.datetime.now())))
    return jsonify({'token': token})

# simple decorator to require admin token in header 'X-ADMIN-TOKEN'
from functools import wraps

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-ADMIN-TOKEN')
        if not token:
            return jsonify({'error':'admin token required'}), 401
        row = query('SELECT * FROM tokens WHERE token = ?', (token,), one=True)
        if not row:
            return jsonify({'error':'invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

# --- Tours CRUD ---

@app.route('/tours', methods=['GET'])
def list_tours():
    rows = query('SELECT * FROM tours')
    tours = [dict(r) for r in rows]
    return jsonify(tours)

@app.route('/tours', methods=['POST'])
@require_admin
def create_tour():
    data = request.json or {}
    title = data.get('title')
    price = data.get('price')
    description = data.get('description','')
    duration = data.get('duration', 1)
    if not title or price is None:
        return jsonify({'error':'title and price required'}), 400
    tour_id = str(uuid.uuid4())
    execute('INSERT INTO tours (id, title, description, price, duration) VALUES (?, ?, ?, ?, ?)', (tour_id, title, description, price, duration))
    return jsonify({'id': tour_id}), 201

@app.route('/tours/<int:tour_id>', methods=['GET'])
def get_tour(tour_id):
    row = query('SELECT * FROM tours WHERE id = ?', (tour_id,), one=True)
    if not row:
        return jsonify({'error':'not found'}), 404
    return jsonify(dict(row))

@app.route('/tours/<int:tour_id>', methods=['PUT'])
@require_admin
def update_tour(tour_id):
    data = request.json or {}
    keys = []
    vals = []
    for k in ('title','description','price','duration'):
        if k in data:
            keys.append(f"{k} = ?")
            vals.append(data[k])
    if not keys:
        return jsonify({'error':'no fields provided'}), 400
    vals.append(tour_id)
    sql = f"UPDATE tours SET {', '.join(keys)} WHERE id = ?"
    execute(sql, tuple(vals))
    return jsonify({'ok':True})

@app.route('/tours/<int:tour_id>', methods=['DELETE'])
@require_admin
def delete_tour(tour_id):
    execute('DELETE FROM tours WHERE id = ?', (tour_id,))
    return jsonify({'ok':True})

# --- Registrations ---

@app.route('/registrations', methods=['POST'])
def register_for_tour():
    data = request.json or {}
    tour_id = data.get('tourId')
    user = data.get('user') or {}
    if not tour_id or not user.get('name'):
        return jsonify({'error':'tourId and user.name required'}), 400
    tour = query('SELECT * FROM tours WHERE id = ?', (tour_id,), one=True)
    if not tour:
        return jsonify({'error':'tour not found'}), 404
    # insert or find user
    existing = query('SELECT * FROM users WHERE email = ?', (user.get('email'),), one=True)
    if existing:
        user_id = existing['id']
    else:
        user_id = str(uuid.uuid4())
        execute('INSERT INTO users (id, name, email) VALUES (?, ?, ?)', (user_id, user.get('name'), user.get('email')))
    import datetime
    reg_id = str(uuid.uuid4())
    execute('INSERT INTO registrations (id, user_id, tour_id, registration_date) VALUES (?, ?, ?, ?)', (reg_id, user_id, tour_id, str(datetime.datetime.now())))
    return jsonify({'registration_id': reg_id, 'tour_price': tour['price']})

@app.route('/registrations/tour/<int:tour_id>', methods=['GET'])
@require_admin
def registrations_for_tour(tour_id):
    rows = query('''SELECT r.id, r.registration_date, u.name, u.email
                    FROM registrations r JOIN users u ON r.user_id = u.id
                    WHERE r.tour_id = ?''', (tour_id,))
    return jsonify([dict(r) for r in rows])

# --- Analytics ---

@app.route('/analytics/tour/<int:tour_id>/registrations', methods=['GET'])
@require_admin
def total_registrations(tour_id):
    row = query('SELECT COUNT(*) as bookings FROM registrations WHERE tour_id = ?', (tour_id,), one=True)
    if not row:
        return jsonify({'bookings':0})
    return jsonify({'bookings': row['bookings'] or 0})

@app.route('/analytics/tour/<int:tour_id>/revenue', methods=['GET'])
@require_admin
def total_revenue(tour_id):
    row = query('SELECT COUNT(*) as bookings FROM registrations WHERE tour_id = ?', (tour_id,), one=True)
    tour = query('SELECT price FROM tours WHERE id = ?', (tour_id,), one=True)
    if not tour or not row:
        return jsonify({'revenue': 0})
    revenue = (row['bookings'] or 0) * (tour['price'] or 0)
    return jsonify({'revenue': revenue})

@app.route('/analytics/tour/history', methods=['GET'])
@require_admin
def tour_history():
    rows = query("SELECT * FROM tours")
    res = []
    for t in rows:
        tid = t['id']
        regs = query('SELECT COUNT(*) as bookings FROM registrations WHERE tour_id = ?', (tid,), one=True)
        revenue = (regs['bookings'] or 0) * (t['price'] or 0)
        res.append({**dict(t), 'bookings': regs['bookings'] or 0, 'revenue': revenue})
    return jsonify(res)

# Simple root
@app.route('/')
def root():
    return 'Tourism Flask API running'

if __name__ == '__main__':
    # ensure DB exists
    try:
        import init_db
        init_db.init_db()
    except Exception as e:
        print('Warning: init DB failed', e)
    app.run(host='0.0.0.0', port=5000, debug=True)
