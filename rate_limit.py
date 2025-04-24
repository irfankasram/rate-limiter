from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import threading

app = Flask(__name__)
DB_FILE = "db/config.db"
LOCK = threading.Lock()

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                ip TEXT,
                endpoint TEXT,
                window_start INTEGER,
                count INTEGER,
                rate_limit INTEGER,
                PRIMARY KEY (ip, endpoint)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS endpoint_config (
                endpoint TEXT PRIMARY KEY,
                requests_per_sec INTEGER
            )
        ''')
        conn.commit()

@app.route('/configure', methods=['POST'])
def configure():
    data = request.get_json()
    endpoint = data.get("endpoint")
    requests_per_sec = data.get("requests_per_sec")
    if not endpoint or not isinstance(requests_per_sec, int):
        return jsonify({"error": "Invalid config"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('REPLACE INTO endpoint_config (endpoint, requests_per_sec) VALUES (?, ?)', (endpoint, requests_per_sec))
        conn.commit()
    return jsonify({"message": "Configuration updated"}), 200

@app.route('/<path:endpoint>', methods=['GET'])
def rate_limiter(endpoint):
    ip = request.remote_addr
    now = int(datetime.utcnow().timestamp())

    with LOCK:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT requests_per_sec FROM endpoint_config WHERE endpoint = ?', (endpoint,))
            config = cursor.fetchone()
            if not config:
                return jsonify({"error": "Endpoint not configured"}), 400

            rate_limit = config[0]
            cursor.execute('SELECT window_start, count FROM rate_limits WHERE ip = ? AND endpoint = ?', (ip, endpoint))
            row = cursor.fetchone()

            if row:
                window_start, count = row
                if now == window_start:
                    if count >= rate_limit:
                        return "Too Many Requests", 429
                    count += 1
                else:
                    window_start = now
                    count = 1
            else:
                window_start = now
                count = 1

            cursor.execute('REPLACE INTO rate_limits (ip, endpoint, window_start, count, rate_limit) VALUES (?, ?, ?, ?, ?)',
                           (ip, endpoint, window_start, count, rate_limit))
            conn.commit()

    return "OK", 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
