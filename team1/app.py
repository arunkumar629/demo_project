from flask import Flask, request, render_template, redirect
import sqlite3
import os

app = Flask(__name__)
DB_FILE = 'test.db'

# Ensure DB is initialized
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Read all users
def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows

# Insert a new user
def add_user(name, age):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, age) VALUES (?, ?)', (name, age))
    conn.commit()
    conn.close()

@app.route('/', methods=['GET'])
def index():
    users = get_all_users()
    return render_template('index.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user_route():
    name = request.form.get('name')
    age = request.form.get('age')
    if name and age:
        add_user(name, int(age))
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
