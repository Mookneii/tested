# app.py
from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "/tmp/training_submissions.db"

app = Flask(__name__, static_folder=APP_DIR)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            notes TEXT,
            ip TEXT,
            user_agent TEXT,
            created_at TEXT
        );
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("training_form.html")

@app.route('/submit', methods=['POST'])
def submit():
    if not request.is_json:
        return jsonify({"error": "Expected JSON"}), 400
    data = request.get_json()
    name = (data.get('name') or '').strip()[:200]
    email = (data.get('email') or '').strip()[:200]
    notes = (data.get('notes') or '').strip()[:1000]
    if not name or not email:
        return jsonify({"error": "Name and email required"}), 400

    ip = request.remote_addr or ''
    ua = request.headers.get('User-Agent', '')[:1000]
    created_at = datetime.utcnow().isoformat() + 'Z'

    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO submissions (name, email, notes, ip, user_agent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, notes, ip, ua, created_at))
        conn.commit()
        conn.close()
    except Exception:
        return jsonify({"error": "Server error"}), 500

    return jsonify({"message": "Submission saved (training only)."}), 200

@app.route('/admin/download', methods=['GET'])
def download_csv():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        rows = cur.execute("SELECT id, name, email, notes, ip, user_agent, created_at FROM submissions ORDER BY created_at DESC").fetchall()
        conn.close()
    except Exception:
        return jsonify({"error": "Server error"}), 500

    lines = ["id,name,email,notes,ip,user_agent,created_at"]
    for r in rows:
        escaped = []
        for v in r:
            if v is None:
                escaped.append('')
            else:
                s = str(v).replace('"','""')
                escaped.append(f'"{s}"')
        lines.append(','.join(escaped))

    csv_data = "\n".join(lines)
    return app.response_class(csv_data, mimetype='text/csv',
                              headers={'Content-Disposition':'attachment;filename=submissions.csv'})

if __name__ == '__main__':
    init_db()
    # For local demo only. If you want to allow other devices on LAN, change host below (see notes).
    app.run(host='127.0.0.1', port=5000, debug=False)
