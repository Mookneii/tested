@app.route('/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json(silent=True) or {}
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    name = (data.get('name') or '').strip()[:200]
    email = (data.get('email') or '').strip()[:200]
    notes = (data.get('notes') or '').strip()[:1000]

    if not name or not email:
        return jsonify({"error": "Name and email required"}), 400

    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or ""
    ua = request.headers.get("User-Agent", "")[:1000]
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
    except Exception as e:
        print("DB ERROR:", e)
        return jsonify({"error": "Server error"}), 500

    return jsonify({"message": "Submission saved (training only)."}), 200
