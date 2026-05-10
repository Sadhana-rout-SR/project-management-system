import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('database.db')
cur = conn.cursor()

cur.execute("""
INSERT INTO users(name,email,password,role)
VALUES(?,?,?,?)
""", (
    'Admin',
    'admin@gmail.com',
    generate_password_hash('admin123'),
    'admin'
))

cur.execute("""
INSERT INTO users(name,email,password,role)
VALUES(?,?,?,?)
""", (
    'Sadhana',
    'employee@gmail.com',
    generate_password_hash('employee123'),
    'employee'
))

cur.execute("""
INSERT INTO projects(title,description,created_by)
VALUES(?,?,?)
""", (
    'Task Management System',
    'Final Year Project',
    1
))

cur.execute("""
INSERT INTO tasks(title,description,status,assigned_to,project_id)
VALUES(?,?,?,?,?)
""", (
    'Frontend Design',
    'Create Dashboard UI',
    'Pending',
    2,
    1
))

conn.commit()
conn.close()

print("Data Inserted Successfully")