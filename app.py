from flask import Flask, jsonify, request
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )
    return conn

@app.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT userId, username, email FROM "User";')
    users = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(users)

@app.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO "User" (username, email, passwordHash) VALUES (%s, %s, %s) RETURNING userId;',
        (data['username'], data['email'], data['passwordHash'])
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'userId': user_id}), 201

if __name__ == '__main__':
    app.run(debug=True)