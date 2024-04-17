from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# Database connection parameters
DB_HOST = 'localhost'
DB_NAME_STUDENTS = 'students_database'
DB_NAME_TEACHERS = 'teachers_database'
DB_NAME_COURSES = 'courses_database'
DB_USER = 'postgres'
DB_PASSWORD = '2023501033'

# Function to establish database connection
def connect_to_db(db_name):
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=db_name,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Function to create user table if not exists
def create_table(conn, table_name, table_definition):
    cur = conn.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table_name} {table_definition}")
    conn.commit()
    conn.close()

# Create tables if not exists
def initialize_database():
    create_table(connect_to_db(DB_NAME_STUDENTS), "students", """
        (id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(50))
    """)
    create_table(connect_to_db(DB_NAME_TEACHERS), "teachers", """
        (id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(50))
    """)
    create_table(connect_to_db(DB_NAME_COURSES), "courses", """
        (id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE,
        description TEXT,
        teacher_id INTEGER)
    """)
    create_table(connect_to_db(DB_NAME_STUDENTS), "student_courses", """
        (id SERIAL PRIMARY KEY,
        student_id INTEGER,
        course_id INTEGER,
        FOREIGN KEY (student_id) REFERENCES students(id),
        FOREIGN KEY (course_id) REFERENCES courses(id))
    """)
# Function to create student_courses table if not exists
def create_student_courses_table():
    conn = connect_to_db(DB_NAME_STUDENTS)  # Connect to students database
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_courses (
            id SERIAL PRIMARY KEY,
            student_id INTEGER,
            course_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    """)
    conn.commit()
    conn.close()


@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type')

        if user_type == 'student':
            table_name = 'students'
        elif user_type == 'teacher':
            table_name = 'teachers'
        else:
            error_message = "Invalid user type."
            return render_template('register.html', error=error_message)

        conn = connect_to_db(DB_NAME_STUDENTS)
        cur = conn.cursor()

        cur.execute(f"SELECT * FROM {table_name} WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        if existing_user:
            error_message = "Username already exists. Please choose a different one."
            return render_template('register.html', error=error_message)
        
        cur.execute(f"INSERT INTO {table_name} (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login_page'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user_type = request.form.get('user_type')

    if user_type == 'student':
        table_name = 'students'
    elif user_type == 'teacher':
        table_name = 'teachers'
    else:
        error_message = "Invalid user type."
        return render_template('login.html', error=error_message)

    conn = connect_to_db(DB_NAME_STUDENTS)
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM {table_name} WHERE username = %s AND password = %s", (username, password))
    user = cur.fetchone()
    conn.close()

    if user:
        if user_type == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('course_catalog', username=username))
    else:
        error_message = "Incorrect username or password. Please try again."
        return render_template('login.html', error=error_message)

@app.route('/course_catalog/<username>')
def course_catalog(username):
    conn = connect_to_db(DB_NAME_COURSES)
    cur = conn.cursor()
    cur.execute("SELECT * FROM courses")
    courses = cur.fetchall()
    conn.close()
    return render_template('course_catalog.html', username=username, courses=courses)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

@app.route('/create_course', methods=['POST'])
def create_course():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        teacher_id = request.form['teacher_id']
        
        conn = connect_to_db(DB_NAME_COURSES)
        cur = conn.cursor()
        cur.execute("INSERT INTO courses (name, description, teacher_id) VALUES (%s, %s, %s)", (name, description, teacher_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('teacher_dashboard'))

@app.route('/enroll_course', methods=['POST'])
def enroll_course():
    if request.method == 'POST':
        course_id = request.form['course_id']
        username = request.form['username']
        
        # Check if the student exists in the students table
        conn_students = connect_to_db(DB_NAME_STUDENTS)
        cur_students = conn_students.cursor()
        cur_students.execute("SELECT * FROM students WHERE username = %s", (username,))
        student = cur_students.fetchone()
        conn_students.close()
        
        if not student:
            error_message = f"Student with username {username} does not exist."
            return render_template('error.html', error=error_message)
        
        # Insert enrollment into the database
        conn_courses = connect_to_db(DB_NAME_COURSES)
        cur_courses = conn_courses.cursor()
        cur_courses.execute("INSERT INTO student_courses (student_id, course_id) VALUES (%s, %s)", (student[0], course_id))
        conn_courses.commit()
        conn_courses.close()
        
        # Redirect to student dashboard with updated enrolled courses
        return redirect(url_for('student_dashboard', username=username))


if __name__ == '__main__':
    initialize_database()  # Initialize the database tables
    app.run(debug=True)
