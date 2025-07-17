import os
import asyncio
import sqlite3
import traceback
from flask import Flask, render_template, request, g, flash, redirect, url_for, session
from dotenv import load_dotenv
from mcp_use import MCPAgent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage

# --- Initial Setup ---

load_dotenv()
app = Flask(__name__)
# A secret key is needed for session management
app.secret_key = os.urandom(24)

# --- Database Configuration & Helpers ---

DATABASE = 'va.db'

def get_db():
    """Connects to the SQLite database."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """Closes the database connection at the end of the request."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database by creating the table if it doesn't exist."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        print("Initializing database...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                age INTEGER NOT NULL,
                qualification TEXT NOT NULL,
                city TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()
        print("Database initialized successfully.")

# --- AI Agent Configuration ---

agent = None

def setup_agent():
    """Sets up the AI agent. This is called once on startup."""
    global agent
    if agent is None:
        print("Setting up AI Agent...")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env file. Please add it.")
        
        llm = ChatGroq(
            model_name="llama3-8b-8192",
            groq_api_key=api_key
        )
        
        agent = MCPAgent(llm=llm, max_steps=10)
        print("AI Agent setup complete.")

# --- Flask Routes ---

@app.route('/')
def home():
    """Renders the home page and clears any existing chat history."""
    session.pop('chat_history', None) # Clear history when visiting home
    return render_template('index.html')

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    """Handles the NL2SQL chat interface with stateful conversation history."""
    # Initialize chat history in session if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []

    answer = None
    question = ""
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if not question:
            flash("⛔ Please enter a question.", "error")
        else:
            try:
                # Load history from session
                chat_history = [HumanMessage(content=msg['content']) if msg['role'] == 'user' 
                                else AIMessage(content=msg['content']) 
                                for msg in session['chat_history']]

                # Append the new user question to the history for the agent
                chat_history.append(HumanMessage(content=question))

                # Run the agent with the full conversation history
                result = asyncio.run(agent.run(chat_history))
                
                if "Agent stopped" in result:
                    flash("❌ The agent could not determine a final answer. Please try rephrasing.", "error")
                else:
                    answer = str(result)
                    # Save the new question and answer to the session history
                    session['chat_history'].append({'role': 'user', 'content': question})
                    session['chat_history'].append({'role': 'assistant', 'content': answer})
                    session.modified = True # Mark session as modified

            except Exception as e:
                error_message = f"❌ An unexpected error occurred: {e}\n\n{traceback.format_exc()}"
                flash(error_message, "error")

    # Pass the history to the template to display the conversation
    return render_template('chat.html', question=question, answer=answer, chat_history=session.get('chat_history', []))

@app.route('/register', methods=['POST'])
def submit_registration():
    """Handles the submission of the course registration form."""
    try:
        name = request.form['name']
        course = request.form['course']
        age = request.form['age']
        qualification = request.form['qualification']
        city = request.form['city']

        if not all([name, course, age, qualification, city]):
            flash("All registration fields are required.", "error")
        else:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO course_registrations (name, course, age, qualification, city) VALUES (?, ?, ?, ?, ?)',
                (name, course, int(age), qualification, city)
            )
            db.commit()
            flash("✅ Registration submitted successfully!", "success")

    except sqlite3.Error as e:
        flash(f"❌ Database error during registration: {e}", "error")
    except ValueError:
        flash("❌ Invalid age. Please enter a number.", "error")
    except Exception as e:
        flash(f"❌ An unexpected error occurred: {e}", "error")

    return redirect(url_for('home'))

# --- Application Startup ---

if __name__ == '__main__':
    init_db()
    setup_agent()
    app.run(debug=True, port=5001)