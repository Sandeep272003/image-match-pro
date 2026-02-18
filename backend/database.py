import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            type TEXT,
            img1_name TEXT,
            img2_name TEXT,
            face_similarity REAL,
            final_score REAL,
            is_same_person INTEGER,
            img1_path TEXT,
            img2_path TEXT,
            cleaned_path TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized")

def save_entry(data):
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO history 
        (timestamp, type, img1_name, img2_name, face_similarity, final_score, 
         is_same_person, img1_path, img2_path, cleaned_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        data.get('type', 'unknown'),
        data.get('img1_name'),
        data.get('img2_name'),
        data.get('face_similarity', 0.0),
        data.get('final_score', 0.0),
        data.get('is_same_person', 0),
        data.get('img1_path'),
        data.get('img2_path'),
        data.get('cleaned_path')
    ))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT 50")
    rows = c.fetchall()
    conn.close()
    return rows

def get_comparison_result(comparison_id):
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("SELECT face_similarity, final_score, is_same_person FROM history WHERE id = ? AND type = 'comparison'", (comparison_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "face_similarity": round(row[0] * 100, 2),
            "final_similarity": round(row[1] * 100, 2),
            "is_same_person": bool(row[2])
        }
    return None

def get_clean_result(clean_id):
    conn = sqlite3.connect("history.db")
    c = conn.cursor()
    c.execute("SELECT img1_path, cleaned_path FROM history WHERE id = ? AND type = 'cleaning'", (clean_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "original_path": row[0],
            "cleaned_path": row[1]
        }
    return None