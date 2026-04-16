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

# User Endpoints
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

# Course Endpoints
@app.route('/courses', methods=['GET'])
def get_courses():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT courseId, userId, title, instructor, term FROM "Course";')
    courses = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(courses)

@app.route('/courses', methods=['POST'])
def add_course():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO "Course" (userId, title, instructor, term) VALUES (%s, %s, %s, %s) RETURNING courseId;',
        (data['userId'], data['title'], data['instructor'], data['term'])
    )
    course_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'courseId': course_id}), 201

@app.route('/courses/<int:course_id>', methods=['PUT'])
def update_course(course_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE "Course" SET title=%s, instructor=%s, term=%s WHERE courseId=%s;',
        (data['title'], data['instructor'], data['term'], course_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Course updated'})

@app.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "Course" WHERE courseId=%s;', (course_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Course deleted'})

# Assignment Endpoints
@app.route('/assignments', methods=['GET'])
def get_assignments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT assignmentId, courseId, title, description, dueDate, status, difficulty, estimatedHours FROM "Assignment";')
    assignments = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(assignments)

@app.route('/assignments', methods=['POST'])
def add_assignment():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO "Assignment" 
        (courseId, title, description, dueDate, status, difficulty, estimatedHours)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING assignmentId;
        ''',
        (
            data['courseId'],
            data['title'],
            data.get('description'),
            data.get('dueDate'),
            data.get('status'),
            data.get('difficulty'),
            data.get('estimatedHours')
        )
    )
    assignment_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'assignmentId': assignment_id}), 201

@app.route('/assignments/<int:assignment_id>', methods=['PUT'])
def update_assignment(assignment_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        UPDATE "Assignment"
        SET title=%s, description=%s, dueDate=%s, status=%s, difficulty=%s, estimatedHours=%s
        WHERE assignmentId=%s;
        ''',
        (
            data['title'],
            data.get('description'),
            data.get('dueDate'),
            data.get('status'),
            data.get('difficulty'),
            data.get('estimatedHours'),
            assignment_id
        )
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Assignment updated'})

@app.route('/assignments/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM "Assignment" WHERE assignmentId=%s;', (assignment_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Assignment deleted'})

# Get assignments for a specific course
@app.route('/courses/<int:course_id>/assignments', methods=['GET'])
def get_assignments_for_course(course_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT assignmentId, title, dueDate, status, difficulty FROM "Assignment" WHERE courseId=%s;',
        (course_id,)
    )
    assignments = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(assignments)

# Get assignments due within the next 7 days
@app.route('/assignments/due-soon', methods=['GET'])
def get_due_soon():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT assignmentId, title, dueDate 
        FROM "Assignment"
        WHERE dueDate BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days';
        '''
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)



# Launch the Flask app
if __name__ == '__main__':
    app.run(debug=True)