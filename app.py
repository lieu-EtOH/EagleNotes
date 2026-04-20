from flask import Flask, jsonify, redirect, request, render_template
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = "your-very-secret-key"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

class User(UserMixin):
    def __init__(self, userId, username, email, passwordHash):
        self.id = userId
        self.username = username
        self.email = email
        self.passwordHash = passwordHash

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT userId, username, email, passwordHash FROM "User" WHERE userId=%s;', (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return User(*row)
    return None        

# Registration Endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    email = data['email']
    password = data['password']

    hashed = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO "User" (username, email, passwordHash) VALUES (%s, %s, %s) RETURNING userId;',
                (username, email, hashed))
    user_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'userId': user_id, 'username': username})

# Login Endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data['username']
    password = data['password']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT userId, username, email, passwordHash FROM "User" WHERE username=%s OR email=%s;',
        (username_or_email, username_or_email)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({'error': 'No account found with that username or email'}), 401

    if not check_password_hash(user[3], password):
        return jsonify({'error': 'Incorrect password'}), 401

    login_user(User(*user))
    return jsonify({'message': 'Login successful', 'userId': user[0]})

# Unauthorized handler for Flask-Login
@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login-page')

# Logout Endpoint
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'})

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=os.getenv("DB_PORT")
    )
    return conn

# Registration Page Endpoint
@app.route('/register-page')
def register_page():
    return render_template('register.html')

# Login Page Endpoint
@app.route('/login-page')
def login_page():
    return render_template('login.html')

# Get user info for personal info
@app.route('/user-info/<int:user_id>')
@login_required
def user_info(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT username, email FROM "User" WHERE userId=%s;', (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        return jsonify({"username": row[0], "email": row[1]})
    return jsonify({"error": "User not found"}), 404

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
@login_required
def get_courses():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT courseId, userId, title, instructor, term FROM "Course" WHERE userId=%s;', (current_user.id,))
    courses = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(courses)

@app.route('/courses', methods=['POST'])
@login_required
def add_course():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO "Course" (userId, title, instructor, term) VALUES (%s, %s, %s, %s) RETURNING courseId;',
        (current_user.id, data['title'], data['instructor'], data['term'])
    )
    course_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'courseId': course_id}), 201

@app.route('/courses/<int:course_id>', methods=['PUT'])
@login_required
def update_course(course_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    # Verify user owns this course
    cur.execute('SELECT userId FROM "Course" WHERE courseId=%s;', (course_id,))
    course = cur.fetchone()
    if not course or course[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute(
        'UPDATE "Course" SET title=%s, instructor=%s, term=%s WHERE courseId=%s;',
        (data['title'], data['instructor'], data['term'], course_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Course updated'})

@app.route('/courses/<int:course_id>', methods=['DELETE'])
@login_required
def delete_course(course_id):
    conn = get_db_connection()
    cur = conn.cursor()
    # Verify user owns this course
    cur.execute('SELECT userId FROM "Course" WHERE courseId=%s;', (course_id,))
    course = cur.fetchone()
    if not course or course[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute('DELETE FROM "Course" WHERE courseId=%s;', (course_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Course deleted'})

@app.route('/courses/search')
@login_required
def search_courses():
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()

    if query:
        cur.execute("""
            SELECT courseId, title, description, instructor
            FROM "Course"
            WHERE userId=%s AND (LOWER(title) LIKE LOWER(%s)
               OR LOWER(description) LIKE LOWER(%s)
               OR LOWER(instructor) LIKE LOWER(%s));
        """, (current_user.id, f"%{query}%", f"%{query}%", f"%{query}%"))
    else:
        cur.execute('SELECT courseId, title, description, instructor FROM "Course" WHERE userId=%s;', (current_user.id,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(results)

# Assignment Endpoints
@app.route('/assignments', methods=['GET'])
@login_required
def get_assignments():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT 
    a.assignmentId,
    a.courseId,
    c.title AS courseTitle,
    a.title,
    a.description,
    a.dueDate,
    a.status,
    a.difficulty,
    a.estimatedHours,
    COALESCE(array_agg(t.name) FILTER (WHERE t.name IS NOT NULL), '{}') AS tags
    FROM "Assignment" a
    JOIN "Course" c ON a.courseId = c.courseId
    LEFT JOIN "AssignmentTag" at ON a.assignmentId = at.assignmentId
    LEFT JOIN "Tag" t ON at.tagId = t.tagId
    WHERE c.userId=%s
    GROUP BY a.assignmentId, c.title;
''', (current_user.id,))
    assignments = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(assignments)


@app.route('/assignments', methods=['POST'])
@login_required
def add_assignment():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns the course
    cur.execute('SELECT userId FROM "Course" WHERE courseId=%s;', (data['courseId'],))
    course = cur.fetchone()
    if not course or course[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
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
            data.get('description') or None,
            data.get('dueDate') or None,
            data.get('status') or None,
            data.get('difficulty') or None,
            data.get('estimatedHours') or None
        )
    )
    assignment_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'assignmentId': assignment_id}), 201

@app.route('/assignments/<int:assignment_id>', methods=['PUT'])
@login_required
def update_assignment(assignment_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this assignment via course
    cur.execute('''
        SELECT c.userId FROM "Assignment" a
        JOIN "Course" c ON a.courseId = c.courseId
        WHERE a.assignmentId=%s;
    ''', (assignment_id,))
    result = cur.fetchone()
    if not result or result[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute(
        '''
        UPDATE "Assignment"
        SET courseId=%s, title=%s, description=%s, dueDate=%s, status=%s, difficulty=%s, estimatedHours=%s
        WHERE assignmentId=%s;
        ''',
        (
            data.get('courseId'),
            data['title'],
            data.get('description') or None,
            data.get('dueDate') or None,
            data.get('status') or None,
            data.get('difficulty') or None,
            data.get('estimatedHours') or None,
            assignment_id
        )
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Assignment updated'})

@app.route('/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this assignment via course
    cur.execute('''
        SELECT c.userId FROM "Assignment" a
        JOIN "Course" c ON a.courseId = c.courseId
        WHERE a.assignmentId=%s;
    ''', (assignment_id,))
    result = cur.fetchone()
    if not result or result[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute('DELETE FROM "Assignment" WHERE assignmentId=%s;', (assignment_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Assignment deleted'})

# Get assignments for a specific course
@app.route('/courses/<int:course_id>/assignments', methods=['GET'])
@login_required
def get_assignments_for_course(course_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns the course
    cur.execute('SELECT userId FROM "Course" WHERE courseId=%s;', (course_id,))
    course = cur.fetchone()
    if not course or course[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
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
@login_required
def get_due_soon():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        '''
        SELECT a.assignmentId, a.title, a.dueDate 
        FROM "Assignment" a
        JOIN "Course" c ON a.courseId = c.courseId
        WHERE c.userId=%s AND a.dueDate BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days';
        ''',
        (current_user.id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(rows)

@app.route('/assignments/search')
@login_required
def search_assignments():
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()

    if query:
        cur.execute("""
            SELECT a.assignmentId, a.courseId, c.title AS courseTitle,
                   a.title, a.description, a.dueDate, a.status,
                   a.difficulty, a.estimatedHours
            FROM "Assignment" a
            JOIN "Course" c ON a.courseId = c.courseId
            WHERE c.userId=%s AND (LOWER(a.title) LIKE LOWER(%s)
               OR LOWER(a.description) LIKE LOWER(%s)
               OR LOWER(c.title) LIKE LOWER(%s))
            ORDER BY a.dueDate ASC;
        """, (current_user.id, f"%{query}%", f"%{query}%", f"%{query}%"))
    else:
        cur.execute("""
            SELECT a.assignmentId, a.courseId, c.title AS courseTitle,
                   a.title, a.description, a.dueDate, a.status,
                   a.difficulty, a.estimatedHours
            FROM "Assignment" a
            JOIN "Course" c ON a.courseId = c.courseId
            WHERE c.userId=%s
            ORDER BY a.dueDate ASC;
        """, (current_user.id,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(results)

# Materials Endpoints
@app.route('/materials', methods=['GET'])
@login_required
def get_materials():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT m.materialId, m.courseId, m.title, m.type, m.filepath 
        FROM "Material" m
        JOIN "Course" c ON m.courseId = c.courseId
        WHERE c.userId=%s;
    ''', (current_user.id,))
    materials = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(materials)

@app.route('/materials', methods=['POST'])
@login_required
def add_material():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns the course
    cur.execute('SELECT userId FROM "Course" WHERE courseId=%s;', (data['courseId'],))
    course = cur.fetchone()
    if not course or course[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute(
        '''
        INSERT INTO "Material" (courseId, title, type, filepath)
        VALUES (%s, %s, %s, %s)
        RETURNING materialId;
        ''',
        (
            data['courseId'],
            data['title'],
            data.get('type'),
            data.get('filepath')
        )
    )
    material_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'materialId': material_id}), 201

@app.route('/materials/<int:material_id>', methods=['PUT'])
@login_required
def update_material(material_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this material via course
    cur.execute('''
        SELECT c.userId FROM "Material" m
        JOIN "Course" c ON m.courseId = c.courseId
        WHERE m.materialId=%s;
    ''', (material_id,))
    result = cur.fetchone()
    if not result or result[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute(
        '''
        UPDATE "Material"
        SET title=%s, type=%s, filepath=%s
        WHERE materialId=%s;
        ''',
        (
            data['title'],
            data.get('type'),
            data.get('filepath'),
            material_id
        )
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Material updated'})

@app.route('/materials/<int:material_id>', methods=['DELETE'])
@login_required
def delete_material(material_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this material via course
    cur.execute('''
        SELECT c.userId FROM "Material" m
        JOIN "Course" c ON m.courseId = c.courseId
        WHERE m.materialId=%s;
    ''', (material_id,))
    result = cur.fetchone()
    if not result or result[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute('DELETE FROM "Material" WHERE materialId=%s;', (material_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Material deleted'})

@app.route('/materials/search')
@login_required
def search_materials():
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()

    if query:
        cur.execute("""
            SELECT m.materialId, m.courseId, c.title AS courseTitle,
                   m.title, m.type, m.filepath
            FROM "Material" m
            JOIN "Course" c ON m.courseId = c.courseId
            WHERE c.userId=%s AND (LOWER(m.title) LIKE LOWER(%s)
               OR LOWER(m.type) LIKE LOWER(%s)
               OR LOWER(c.title) LIKE LOWER(%s));
        """, (current_user.id, f"%{query}%", f"%{query}%", f"%{query}%"))
    else:
        cur.execute("""
            SELECT m.materialId, m.courseId, c.title AS courseTitle,
                   m.title, m.type, m.filepath
            FROM "Material" m
            JOIN "Course" c ON m.courseId = c.courseId
            WHERE c.userId=%s;
        """, (current_user.id,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(results)

#Tags Endpoints
@app.route('/tags', methods=['GET'])
@login_required
def get_tags():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT tagId, name FROM "Tag" WHERE userId=%s;', (current_user.id,))
    tags = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(tags)

@app.route('/tags', methods=['POST'])
@login_required
def add_tag():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO "Tag" (userId, name) VALUES (%s, %s) RETURNING tagId;',
        (current_user.id, data['name'])
    )
    tag_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'tagId': tag_id}), 201

@app.route('/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this tag
    cur.execute('SELECT userId FROM "Tag" WHERE tagId=%s;', (tag_id,))
    tag = cur.fetchone()
    if not tag or tag[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute('DELETE FROM "Tag" WHERE tagId=%s;', (tag_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Tag deleted'})

@app.route('/tags/search')
@login_required
def search_tags():
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    cur = conn.cursor()

    if query:
        cur.execute('SELECT tagId, name FROM "Tag" WHERE userId=%s AND LOWER(name) LIKE LOWER(%s);',
                    (current_user.id, f"%{query}%"))
    else:
        cur.execute('SELECT tagId, name FROM "Tag" WHERE userId=%s;', (current_user.id,))

    results = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(results)

#Join table between tags and assignments
@app.route('/assignments/<int:assignment_id>/tags', methods=['POST'])
@login_required
def add_tag_to_assignment(assignment_id):
    data = request.get_json()
    tag_id = data['tagId']

    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this assignment
    cur.execute('''
        SELECT c.userId FROM "Assignment" a
        JOIN "Course" c ON a.courseId = c.courseId
        WHERE a.assignmentId=%s;
    ''', (assignment_id,))
    result = cur.fetchone()
    if not result or result[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Verify user owns this tag
    cur.execute('SELECT userId FROM "Tag" WHERE tagId=%s;', (tag_id,))
    tag = cur.fetchone()
    if not tag or tag[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute(
        'INSERT INTO "AssignmentTag" (assignmentId, tagId) VALUES (%s, %s);',
        (assignment_id, tag_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Tag added to assignment'}), 201

#Get tags for a specific assignment
@app.route('/assignments/<int:assignment_id>/tags', methods=['GET'])
@login_required
def get_tags_for_assignment(assignment_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this assignment
    cur.execute('''
        SELECT c.userId FROM "Assignment" a
        JOIN "Course" c ON a.courseId = c.courseId
        WHERE a.assignmentId=%s;
    ''', (assignment_id,))
    result = cur.fetchone()
    if not result or result[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute(
        '''
        SELECT t.tagId, t.name
        FROM "Tag" t
        JOIN "AssignmentTag" at ON t.tagId = at.tagId
        WHERE at.assignmentId = %s;
        ''',
        (assignment_id,)
    )
    tags = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(tags)

#Remove a tag from an assignment
@app.route('/assignments/<int:assignment_id>/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def remove_tag_from_assignment(assignment_id, tag_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verify user owns this assignment
    cur.execute('''
        SELECT c.userId FROM "Assignment" a
        JOIN "Course" c ON a.courseId = c.courseId
        WHERE a.assignmentId=%s;
    ''', (assignment_id,))
    result = cur.fetchone()
    if not result or result[0] != current_user.id:
        cur.close()
        conn.close()
        return jsonify({'error': 'Unauthorized'}), 403
    
    cur.execute(
        'DELETE FROM "AssignmentTag" WHERE assignmentId=%s AND tagId=%s;',
        (assignment_id, tag_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Tag removed from assignment'})

# Frontend Routes
from flask import render_template

@app.route('/')
@login_required
def index_page():
    return render_template('index.html')

@app.route('/courses-page')
@login_required
def courses_page():
    return render_template('courses.html')

@app.route('/assignments-page')
@login_required
def assignments_page():
    return render_template('assignments.html')


@app.route('/materials-page')
@login_required
def materials_page():
    return render_template('materials.html')

@app.route('/tags-page')
@login_required
def tags_page():
    return render_template('tags.html')

# Launch the Flask app
if __name__ == '__main__':
    app.run(debug=True)