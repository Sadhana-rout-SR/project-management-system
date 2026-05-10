from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = 'secret123'


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn



def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        created_by INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        status TEXT,
        assigned_to INTEGER,
        project_id INTEGER
    )
    """)

    conn.commit()
    conn.close()


create_tables()


@app.route('/')
def home():
    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE email=?", (email,))
        existing_user = cur.fetchone()

        if existing_user:
            flash("Email already exists")
            return redirect('/register')

        cur.execute("""
        INSERT INTO users(name,email,password,role)
        VALUES(?,?,?,?)
        """, (name, email, password, role))

        conn.commit()
        conn.close()

        flash("Registration Successful")
        return redirect('/')

    return render_template('register.html')



@app.route('/login', methods=['POST'])
def login():

    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cur.fetchone()

    conn.close()

    if user:

        if check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect('/admin_dashboard')
            else:
                return redirect('/dashboard')

    flash("Invalid Email or Password")
    return redirect('/')



@app.route('/admin_dashboard')
def admin_dashboard():

    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM projects")
    projects = cur.fetchall()

    cur.execute("""
    SELECT tasks.id,
           tasks.title,
           tasks.status,
           users.name,
           projects.title
    FROM tasks
    JOIN users ON tasks.assigned_to = users.id
    JOIN projects ON tasks.project_id = projects.id
    """)

    tasks = cur.fetchall()

    conn.close()

    return render_template(
        'admin_dashboard.html',
        projects=projects,
        tasks=tasks
    )


@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT tasks.id,
           tasks.title,
           tasks.description,
           tasks.status,
           projects.title
    FROM tasks
    JOIN projects ON tasks.project_id = projects.id
    WHERE tasks.assigned_to = ?
    """, (user_id,))

    tasks = cur.fetchall()

    conn.close()

    total_tasks = len(tasks)

    completed_tasks = 0
    pending_tasks = 0

    for task in tasks:

        if task['status'] == 'Completed':
            completed_tasks += 1
        else:
            pending_tasks += 1

    return render_template(
        'dashboard.html',
        tasks=tasks,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks
    )


@app.route('/create_project', methods=['GET', 'POST'])
def create_project():

    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO projects(title, description, created_by)
        VALUES(?,?,?)
        """, (title, description, session['user_id']))

        conn.commit()
        conn.close()

        flash("Project Created")
        return redirect('/admin_dashboard')

    return render_template('create_project.html')


@app.route('/create_task', methods=['GET', 'POST'])
def create_task():

    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE role='employee'")
    users = cur.fetchall()

    cur.execute("SELECT * FROM projects")
    projects = cur.fetchall()

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        project_id = request.form['project_id']

        cur.execute("""
        INSERT INTO tasks(title, description, status, assigned_to, project_id)
        VALUES(?,?,?,?,?)
        """, (title, description, 'Pending', assigned_to, project_id))

        conn.commit()
        conn.close()

        flash("Task Created")
        return redirect('/admin_dashboard')

    return render_template(
        'create_task.html',
        users=users,
        projects=projects
    )


@app.route('/update_status/<int:id>')
def update_status(id):

    if 'user_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE tasks
    SET status='Completed'
    WHERE id=?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Task Completed")
    return redirect('/dashboard')



@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)