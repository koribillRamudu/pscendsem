from flask import Flask, render_template, request, redirect, url_for
import psycopg2

app = Flask(__name__)

# Database connection parameters
DB_HOST = 'localhost'
DB_NAME_STUDENTS = 'students_database'
DB_NAME_TEACHERS = 'teachers_database'
DB_USER = 'postgres'
DB_PASSWORD = '2023501033'

# Function to establish database connection for students
def connect_to_students_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME_STUDENTS,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Function to establish database connection for teachers
def connect_to_teachers_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME_TEACHERS,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn

# Function to create user table if not exists for students
def create_students_table():
    conn = connect_to_students_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(50)
        )
    """)
    conn.commit()
    conn.close()

# Function to create user table if not exists for teachers
def create_teachers_table():
    conn = connect_to_teachers_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(50)
        )
    """)
    conn.commit()
    conn.close()

# Initialize user tables
create_students_table()
create_teachers_table()

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user is a student or a teacher
        user_type = request.form.get('user_type')

        if user_type == 'student':
            conn = connect_to_students_db()
            table_name = 'students'
        elif user_type == 'teacher':
            conn = connect_to_teachers_db()
            table_name = 'teachers'
        else:
            error_message = "Invalid user type."
            return render_template('register.html', error=error_message)

        cur = conn.cursor()

        # Check if username already exists
        cur.execute(f"SELECT * FROM {table_name} WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        if existing_user:
            error_message = "Username already exists. Please choose a different one."
            return render_template('register.html', error=error_message)
        
        # Insert new user into the database
        cur.execute(f"INSERT INTO {table_name} (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        conn.close()

        return redirect(url_for('login_page'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Check if the user is a student or a teacher
    user_type = request.form.get('user_type')

    if user_type == 'student':
        conn = connect_to_students_db()
        table_name = 'students'
    elif user_type == 'teacher':
        conn = connect_to_teachers_db()
        table_name = 'teachers'
    else:
        error_message = "Invalid user type."
        return render_template('login.html', error=error_message)

    cur = conn.cursor()

    # Check if username and password match
    cur.execute(f"SELECT * FROM {table_name} WHERE username = %s AND password = %s", (username, password))
    user = cur.fetchone()
    conn.close()

    if user:
        return redirect(url_for('dashboard'))
    else:
        error_message = "Incorrect username or password. Please try again."
        return render_template('login.html', error=error_message)

@app.route('/dashboard')
def dashboard():
    return "Welcome to the dashboard!"

if __name__ == '__main__':
    app.run(debug=True)
