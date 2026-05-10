from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = 'secret123'

# MYSQL CONFIG
app.config['MYSQL_HOST'] = 'containers-us-west-xx.railway.app'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'abcd123'
app.config['MYSQL_DB'] = 'railway'

mysql = MySQL(app)

# ================= HOME =================
@app.route('/')
def home():
    return render_template('login.html')


# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        cur = mysql.connection.cursor()

        # CHECK DUPLICATE EMAIL
        cur.execute("SELECT * FROM users WHERE email=%s", [email])
        existing_user = cur.fetchone()

        if existing_user:
            flash("Email already exists")
            return redirect('/register')

        cur.execute("""
        INSERT INTO users(name,email,password,role)
        VALUES(%s,%s,%s,%s)
        """, (name, email, password, role))

        mysql.connection.commit()
        cur.close()

        flash("Registration Successful")
        return redirect('/')

    return render_template('register.html')


# ================= LOGIN =================
@app.route('/login', methods=['POST'])
def login():

    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM users WHERE email=%s", [email])

    user = cur.fetchone()

    if user:

        if check_password_hash(user[3], password):

            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = user[4]

            if user[4] == 'admin':
                return redirect('/admin_dashboard')

            else:
                return redirect('/dashboard')

    flash("Invalid Email or Password")
    return redirect('/')


# ================= ADMIN DASHBOARD =================
@app.route('/admin_dashboard')
def admin_dashboard():

    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    cur = mysql.connection.cursor()

    # PROJECTS
    cur.execute("SELECT * FROM projects")
    projects = cur.fetchall()

    # TASKS
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

    return render_template(
        'admin_dashboard.html',
        projects=projects,
        tasks=tasks
    )


# ================= EMPLOYEE DASHBOARD =================
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    cur.execute("""
    SELECT tasks.id,
           tasks.title,
           tasks.description,
           tasks.status,
           projects.title
    FROM tasks
    JOIN projects ON tasks.project_id = projects.id
    WHERE tasks.assigned_to = %s
    """, [user_id])

    tasks = cur.fetchall()

    # COUNT TASKS
    total_tasks = len(tasks)

    completed_tasks = 0
    pending_tasks = 0

    for task in tasks:

        if task[3] == 'Completed':
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


# ================= CREATE PROJECT =================
@app.route('/create_project', methods=['GET', 'POST'])
def create_project():

    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']

        cur = mysql.connection.cursor()

        cur.execute("""
        INSERT INTO projects(title, description, created_by)
        VALUES(%s, %s, %s)
        """, (title, description, session['user_id']))

        mysql.connection.commit()

        flash("Project Created")
        return redirect('/admin_dashboard')

    return render_template('create_project.html')


# ================= CREATE TASK =================
@app.route('/create_task', methods=['GET', 'POST'])
def create_task():

    if 'role' not in session or session['role'] != 'admin':
        return redirect('/')

    cur = mysql.connection.cursor()

    # ONLY EMPLOYEES
    cur.execute("SELECT * FROM users WHERE role='employee'")
    users = cur.fetchall()

    # PROJECTS
    cur.execute("SELECT * FROM projects")
    projects = cur.fetchall()

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        project_id = request.form['project_id']

        cur.execute("""
        INSERT INTO tasks(title, description, status, assigned_to, project_id)
        VALUES(%s, %s, %s, %s, %s)
        """, (title, description, 'Pending', assigned_to, project_id))

        mysql.connection.commit()

        flash("Task Created")
        return redirect('/admin_dashboard')

    return render_template(
        'create_task.html',
        users=users,
        projects=projects
    )


# ================= UPDATE TASK STATUS =================
@app.route('/update_status/<int:id>')
def update_status(id):

    if 'user_id' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()

    # UPDATE ONLY EMPLOYEE TASK
    cur.execute("""
    UPDATE tasks
    SET status='Completed'
    WHERE id=%s
    """, [id])

    mysql.connection.commit()

    flash("Task Completed")
    return redirect('/dashboard')


# ================= LOGOUT =================
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)