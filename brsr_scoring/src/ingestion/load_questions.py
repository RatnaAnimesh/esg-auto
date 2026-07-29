import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "brsr.db"
QUESTIONS_FILE = BASE_DIR / "data" / "questions.txt"

def load_questions():
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return
        
    if not QUESTIONS_FILE.exists():
        print(f"Questions file not found at {QUESTIONS_FILE}")
        return

    print("Loading questions from text file...")
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    questions = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Split "1. What is..." into "Q1" and "What is..."
        parts = line.split(". ", 1)
        if len(parts) == 2:
            q_id = f"Q{parts[0]}"
            q_text = parts[1]
            questions.append((q_id, q_text, 'numeric')) # default to numeric for now or text
            
    print(f"Found {len(questions)} questions.")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        print("Inserting into Question_Master...")
        for q_id, q_text, d_type in questions:
            cur.execute("""
                INSERT OR REPLACE INTO Question_Master (question_id, question_text, data_type)
                VALUES (?, ?, ?)
            """, (q_id, q_text, d_type))
        conn.commit()
    print("Successfully populated Question_Master.")

if __name__ == "__main__":
    load_questions()
