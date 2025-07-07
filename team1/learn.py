import sqlite3

# Connect to SQLite database (it will be created if it doesn't exist)
conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# 1. Create a table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL
)
''')

# 2. Insert data into the table
users_data = [
    ('Alice', 25),
    ('Bob', 30),
    ('Charlie', 22)
]

cursor.executemany('INSERT INTO users (name, age) VALUES (?, ?)', users_data)
conn.commit()

# 3. Read data from the table
cursor.execute('SELECT * FROM users')
rows = cursor.fetchall()

print("Users Table:")
for row in rows:
    print(row)

# Close the connection
conn.close()
