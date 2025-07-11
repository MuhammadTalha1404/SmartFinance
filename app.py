from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from datetime import datetime, timedelta
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import secrets
import re
import random
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup
def init_db():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        age INTEGER,
        occupation TEXT,
        income REAL,
        location TEXT,
        financial_goals_summary TEXT,
        profile_picture TEXT
    )''')
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if 'age' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN age INTEGER')
    if 'occupation' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN occupation TEXT')
    if 'income' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN income REAL')
    if 'location' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN location TEXT')
    if 'financial_goals_summary' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN financial_goals_summary TEXT')
    if 'profile_picture' not in columns:
        c.execute('ALTER TABLE users ADD COLUMN profile_picture TEXT')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        category TEXT,
        amount REAL,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category TEXT,
        amount REAL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        description TEXT,
        target_amount REAL,
        current_amount REAL,
        deadline TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        description TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if not c.fetchone():
        c.execute('INSERT INTO users (username, first_name, last_name, email, password, is_admin) VALUES (?, ?, ?, ?, ?, ?)',
                  ('admin', 'Admin', 'User', 'admin@smartfinance.com', generate_password_hash('Admin@1234'), 1))
    conn.commit()
    conn.close()

    # Ensure uploads directory exists
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')

init_db()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, is_admin=False, age=None, occupation=None, income=None, location=None, financial_goals_summary=None, profile_picture=None):
        self.id = id
        self.username = username
        self.is_admin = is_admin
        self.age = age
        self.occupation = occupation
        self.income = income
        self.location = location
        self.financial_goals_summary = financial_goals_summary
        self.profile_picture = profile_picture

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT id, username, is_admin, age, occupation, income, location, financial_goals_summary, profile_picture FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(id=user_data[0], username=user_data[1], is_admin=user_data[2], age=user_data[3], occupation=user_data[4], 
                   income=user_data[5], location=user_data[6], financial_goals_summary=user_data[7], profile_picture=user_data[8])
    return None

# Admin required decorator
def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        
        if len(password) < 8 or not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not any(c.isdigit() for c in password) or not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            flash('Password must be at least 8 characters with uppercase, lowercase, numbers, and special characters.')
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        conn = sqlite3.connect('smartfinance.db')
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, first_name, last_name, email, password, is_admin) VALUES (?, ?, ?, ?, ?, 0)',
                      (username, first_name, last_name, email, password_hash))
            conn.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists.')
        conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('smartfinance.db')
        c = conn.cursor()
        c.execute('SELECT id, password, is_admin FROM users WHERE username = ?', (username,))
        user_data = c.fetchone()
        conn.close()
        if user_data and check_password_hash(user_data[1], password):
            user = User(id=user_data[0], username=username, is_admin=user_data[2])
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT type, category, amount, date FROM transactions WHERE user_id = ?', (current_user.id,))
    transactions = c.fetchall()
    c.execute('SELECT category, amount FROM budgets WHERE user_id = ?', (current_user.id,))
    budgets = c.fetchall()
    conn.close()

    df = pd.DataFrame(transactions, columns=['type', 'category', 'amount', 'date'])
    total_income = df[df['type'] == 'income']['amount'].sum() if not df.empty and 'income' in df['type'].values else 0
    total_expenses = df[df['type'] == 'expense']['amount'].sum() if not df.empty and 'expense' in df['type'].values else 0
    current_balance = total_income - total_expenses

    # Generate spending chart and handle empty data
    spending_data = {}
    if not df.empty and 'expense' in df['type'].values:
        spending = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
        plt.figure(figsize=(6, 6))
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
        plt.pie(spending, labels=spending.index, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Spending by Category', color='#26A69A', fontsize=14)
        plt.axis('equal')
        plt.savefig('static/spending_chart.png')
        plt.close()
        spending_data = spending.to_dict()
    else:
        spending_data = {}

    # Recent activities (last 5 transactions)
    recent_transactions = transactions[-5:] if transactions else []

    return render_template('dashboard.html', total_income=total_income, total_expenses=total_expenses, 
                          current_balance=current_balance, spending=spending_data, recent_transactions=recent_transactions)

    # Generate spending chart
    if not df.empty:
        spending = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
        plt.figure(figsize=(6, 6))
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
        plt.pie(spending, labels=spending.index, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Spending by Category', color='#26A69A', fontsize=14)
        plt.axis('equal')
        plt.savefig('static/spending_chart.png')
        plt.close()
    else:
        spending = {}

    # Recent activities (last 5 transactions)
    recent_transactions = transactions[-5:] if transactions else []

    return render_template('dashboard.html', total_income=total_income, total_expenses=total_expenses, 
                          current_balance=current_balance, spending=spending, recent_transactions=recent_transactions)

@app.route('/transactions')
@login_required
def transactions():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT id, type, category, amount, date FROM transactions WHERE user_id = ?', (current_user.id,))
    transactions = c.fetchall()
    conn.close()

    df = pd.DataFrame(transactions, columns=['id', 'type', 'category', 'amount', 'date'])
    chart_exists = False
    if not df.empty:
        spending = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
        plt.figure(figsize=(6, 6))
        colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
        plt.pie(spending, labels=spending.index, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Spending by Category', color='#26A69A', fontsize=14)
        plt.axis('equal')
        plt.savefig('static/spending_chart.png')
        plt.close()
        chart_exists = True

    return render_template('transactions.html', transactions=transactions, chart_exists=chart_exists)

@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    type_ = request.form['type']
    category = request.form['category']
    amount = float(request.form['amount'])
    date = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)',
              (current_user.id, type_, category, amount, date))
    conn.commit()
    conn.close()
    flash('Transaction added.')
    return redirect(url_for('transactions'))

@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        type_ = request.form['type']
        category = request.form['category']
        amount = float(request.form['amount'])
        date = request.form['date']  # Allow custom date input
        c.execute('UPDATE transactions SET type = ?, category = ?, amount = ?, date = ? WHERE id = ? AND user_id = ?',
                  (type_, category, amount, date, transaction_id, current_user.id))
        conn.commit()
        conn.close()
        flash('Transaction updated successfully.')
        return redirect(url_for('transactions'))
    
    # GET request: Fetch transaction details for the form
    c.execute('SELECT type, category, amount, date FROM transactions WHERE id = ? AND user_id = ?', (transaction_id, current_user.id,))
    transaction = c.fetchone()
    conn.close()
    
    if transaction is None:
        flash('Transaction not found or access denied.')
        return redirect(url_for('transactions'))
    
    return render_template('edit_transaction.html', transaction=transaction, transaction_id=transaction_id)

@app.route('/budgets')
@login_required
def budgets():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT id, category, amount FROM budgets WHERE user_id = ?', (current_user.id,))
    budgets = c.fetchall()
    conn.close()
    return render_template('budgets.html', budgets=budgets)

@app.route('/set_budget', methods=['POST'])
@login_required
def set_budget():
    category = request.form['category']
    amount = float(request.form['amount'])
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO budgets (user_id, category, amount) VALUES (?, ?, ?)',
              (current_user.id, category, amount))
    conn.commit()
    conn.close()
    flash('Budget set successfully.')
    return redirect(url_for('budgets'))

@app.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def user_edit_budget(budget_id):  # Renamed to avoid conflict
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        c.execute('UPDATE budgets SET category = ?, amount = ? WHERE id = ? AND user_id = ?',
                  (category, amount, budget_id, current_user.id))
        conn.commit()
        conn.close()
        flash('Budget updated successfully.')
        return redirect(url_for('budgets'))
    
    # GET request: Fetch budget details for the form
    c.execute('SELECT category, amount FROM budgets WHERE id = ? AND user_id = ?', (budget_id, current_user.id,))
    budget = c.fetchone()
    conn.close()
    
    if budget is None:
        flash('Budget not found or access denied.')
        return redirect(url_for('budgets'))
    
    return render_template('edit_budget.html', budget=budget, budget_id=budget_id)

@app.route('/goals')
@login_required
def goals():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT description, target_amount, current_amount, deadline FROM goals WHERE user_id = ?', (current_user.id,))
    goals = c.fetchall()
    conn.close()
    return render_template('goals.html', goals=goals)

@app.route('/set_goal', methods=['POST'])
@login_required
def set_goal():
    description = request.form['description']
    target_amount = float(request.form['target_amount'])
    deadline = request.form['deadline']
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('INSERT INTO goals (user_id, description, target_amount, current_amount, deadline) VALUES (?, ?, ?, 0, ?)',
              (current_user.id, description, target_amount, deadline))
    conn.commit()
    conn.close()
    flash('Goal set.')
    return redirect(url_for('goals'))

@app.route('/reminders')
@login_required
def reminders():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT description, date FROM reminders WHERE user_id = ?', (current_user.id,))
    reminders = c.fetchall()
    conn.close()
    return render_template('reminders.html', reminders=reminders)

@app.route('/set_reminder', methods=['POST'])
@login_required
def set_reminder():
    description = request.form['description']
    date = request.form['date']
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('INSERT INTO reminders (user_id, description, date) VALUES (?, ?, ?)',
              (current_user.id, description, date))
    conn.commit()
    conn.close()
    flash('Reminder set.')
    return redirect(url_for('reminders'))

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/predict_spending')
@login_required
def predict_spending():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT amount, date FROM transactions WHERE user_id = ? AND type = "expense"', (current_user.id,))
    data = c.fetchall()
    conn.close()

    if len(data) < 2:
        flash('Not enough data for prediction.')
        return redirect(url_for('reports'))

    df = pd.DataFrame(data, columns=['amount', 'date'])
    df['date'] = pd.to_datetime(df['date'])
    df['days'] = (df['date'] - df['date'].min()).dt.days
    X = df[['days']].values
    y = df['amount'].values
    model = LinearRegression()
    model.fit(X, y)
    next_month = max(df['days']) + 30
    predicted = model.predict([[next_month]])[0]
    flash(f'Predicted spending next month: ${predicted:.2f}')
    return redirect(url_for('reports'))

@app.route('/estimate_tax')
@login_required
def estimate_tax():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT amount FROM transactions WHERE user_id = ? AND type = "income"', (current_user.id,))
    income_data = c.fetchall()
    conn.close()

    total_income = sum(t[0] for t in income_data) if income_data else 0
    tax_rate = 0.10
    estimated_tax = total_income * tax_rate
    flash(f'Estimated tax: ${estimated_tax:.2f} (based on {total_income:.2f} income at {tax_rate*100}% rate)')
    return redirect(url_for('reports'))

@app.route('/export_pdf/<period>')
@login_required
def export_pdf(period):
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT type, category, amount, date FROM transactions WHERE user_id = ?', (current_user.id,))
    transactions = c.fetchall()
    conn.close()

    df = pd.DataFrame(transactions, columns=['type', 'category', 'amount', 'date'])
    df['date'] = pd.to_datetime(df['date'])

    if period == 'weekly':
        start_date = df['date'].max() - pd.Timedelta(days=7)
        df = df[df['date'] >= start_date]
        title = 'Weekly Report'
    elif period == 'yearly':
        start_date = df['date'].min().replace(month=1, day=1)
        df = df[df['date'] >= start_date]
        title = 'Yearly Report'
    else:
        start_date = df['date'].max().replace(day=1)
        df = df[df['date'] >= start_date]
        title = 'Monthly Report'

    pdf_file = f'static/report_{current_user.id}_{period}.pdf'
    c = canvas.Canvas(pdf_file, pagesize=letter)
    c.drawString(100, 750, f'{title} for {current_user.username}')
    y = 700
    for t in df.itertuples(index=False):
        c.drawString(100, y, f'{t.date} | {t.type} | {t.category} | ${t.amount:.2f}')
        y -= 20
        if y < 50:
            c.showPage()
            y = 700
    c.save()
    return send_file(pdf_file, as_attachment=True)

@app.route('/profile')
@login_required
def profile():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT username, age, occupation, income, location, financial_goals_summary, profile_picture FROM users WHERE id = ?', (current_user.id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        username, age, occupation, income, location, financial_goals_summary, profile_picture = user_data
    else:
        username = current_user.username
        age, occupation, income, location, financial_goals_summary, profile_picture = None, None, None, None, None, None
    return render_template('profile.html', username=username, age=age, occupation=occupation, income=income, 
                          location=location, financial_goals_summary=financial_goals_summary, profile_picture=profile_picture)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    age = request.form.get('age')
    occupation = request.form.get('occupation')
    income = request.form.get('income')
    location = request.form.get('location')
    financial_goals_summary = request.form.get('financial_goals_summary')

    # Handle profile picture upload
    profile_picture = request.files.get('profile_picture')
    picture_filename = None
    if profile_picture and profile_picture.filename:
        filename = secure_filename(profile_picture.filename)
        picture_filename = f"profile_{current_user.id}_{filename}"
        profile_picture.save(os.path.join('static/uploads', picture_filename))

    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    update_query = 'UPDATE users SET age = ?, occupation = ?, income = ?, location = ?, financial_goals_summary = ?'
    params = [age if age else None, occupation if occupation else None, 
              float(income) if income else None, location if location else None, 
              financial_goals_summary if financial_goals_summary else None]
    if picture_filename:
        update_query += ', profile_picture = ?'
        params.append(picture_filename)
    update_query += ' WHERE id = ?'
    params.append(current_user.id)

    try:
        c.execute(update_query, params)
        conn.commit()
        flash('Profile updated successfully.')
    except (ValueError, sqlite3.Error) as e:
        flash(f'Error updating profile: {str(e)}')
    finally:
        conn.close()

    # Update current_user object to reflect changes
    current_user.age = age
    current_user.occupation = occupation
    current_user.income = float(income) if income else None
    current_user.location = location
    current_user.financial_goals_summary = financial_goals_summary
    current_user.profile_picture = picture_filename

    return redirect(url_for('profile'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/chat_process', methods=['POST'])
@login_required
def chat_process():
    user_query = request.json.get('query', '').lower().strip()
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT type, category, amount, date FROM transactions WHERE user_id = ?', (current_user.id,))
    transactions = c.fetchall()
    c.execute('SELECT category, amount FROM budgets WHERE user_id = ?', (current_user.id,))
    budgets = c.fetchall()
    c.execute('SELECT description, target_amount, current_amount, deadline FROM goals WHERE user_id = ?', (current_user.id,))
    goals = c.fetchall()
    c.execute('SELECT description, date FROM reminders WHERE user_id = ?', (current_user.id,))
    reminders = c.fetchall()
    conn.close()

    df = pd.DataFrame(transactions, columns=['type', 'category', 'amount', 'date'])
    response = "I'm not sure I understood that. Could you ask about your finances, daily tasks, or something else? I'm here to assist, {}!".format(current_user.username)

    # Intent detection using regex patterns
    patterns = {
        'greeting': r'\b(hi|hello|hey|howdy)\b',
        'spending': r'\b(spend|spent|expense|spending|how much)\b',
        'budget': r'\b(budget|budgets|limit|plan)\b',
        'goal': r'\b(goal|goals|save|saving|target)\b',
        'reminder': r'\b(reminder|remind|task|todo)\b',
        'weather': r'\b(weather|forecast|temperature)\b',
        'motivation': r'\b(motivation|motivate|inspire|quote)\b',
        'joke': r'\b(joke|funny|laugh)\b',
        'advice': r'\b(advice|tip|help|guide|suggest)\b',
        'balance': r'\b(balance|net worth|total|summary)\b',
        'category_spending': r'\b(spend|spent|expense).*?(category|categories)\b',
        'savings_tip': r'\b(save|saving|tips|how to save)\b',
        'daily_tip': r'\b(daily|life|routine|productivity)\b',
        'time': r'\b(time|what time|current time)\b'
    }

    # Helper functions for financial analysis
    def get_category_spending(df, category):
        category_df = df[(df['type'] == 'expense') & (df['category'].str.lower() == category.lower())]
        total = category_df['amount'].sum()
        return total

    def get_monthly_summary(df):
        df['date'] = pd.to_datetime(df['date'])
        current_month = datetime.now().strftime('%Y-%m')
        monthly_df = df[df['date'].dt.strftime('%Y-%m') == current_month]
        income = monthly_df[monthly_df['type'] == 'income']['amount'].sum()
        expenses = monthly_df[monthly_df['type'] == 'expense']['amount'].sum()
        return income, expenses

    def get_savings_tips(df, budgets):
        tips = []
        if not df.empty:
            expenses = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
            for cat, amt in expenses.items():
                budget = next((b[1] for b in budgets if b[0].lower() == cat.lower()), None)
                if budget and amt > budget:
                    tips.append(f"You're over budget in {cat} by ${amt - budget:.2f}. Consider cutting back on non-essential spending.")
        tips.append("Save 10-20% of your income each month for emergencies or investments.")
        return tips if tips else ["No specific tips, but try saving a fixed percentage of your income regularly!"]

    # Mock responses for external data
    mock_weather = "It's sunny with a high of 75°F in your area today. Perfect for a walk!"
    motivational_quotes = [
        "The journey of a thousand miles begins with a single step.",
        "Stay focused and never give up on your dreams!",
        "Every day is a new opportunity to grow and succeed."
    ]
    jokes = [
        "Why did the scarecrow become a motivational speaker? Because he was outstanding in his field!",
        "Why don't eggs tell jokes? They'd crack up!",
        "What do you call a bear with no socks on? Barefoot!"
    ]

    # Process query based on intent
    if re.search(patterns['greeting'], user_query):
        response = f"Hey there, {current_user.username}! What's on your mind today? Finances, daily tasks, or just a chat?"
    elif re.search(patterns['spending'], user_query):
        if df.empty:
            response = "You haven't recorded any expenses yet. Want to add some transactions to track your spending?"
        else:
            total_spending = df[df['type'] == 'expense']['amount'].sum()
            this_month = df[df['date'].str.startswith(datetime.now().strftime('%Y-%m'))]['amount'].sum()
            response = f"You've spent ${total_spending:.2f} overall, and ${this_month:.2f} this month. Need a breakdown by category?"
    elif re.search(patterns['category_spending'], user_query):
        for category in df['category'].unique():
            if category.lower() in user_query:
                total = get_category_spending(df, category)
                response = f"You've spent ${total:.2f} on {category}. Want tips to manage this category?"
                break
        else:
            response = "Which category would you like to know about? For example, try 'How much did I spend on Food?'"
    elif re.search(patterns['budget'], user_query):
        if not budgets:
            response = "You haven't set any budgets yet. Go to the Budgets page to create one and stay on track!"
        else:
            budget_status = ', '.join(f"{cat}: ${amt:.2f}" for cat, amt in budgets)
            response = f"Your budgets are: {budget_status}. Want to adjust them or get tips?"
    elif re.search(patterns['goal'], user_query):
        if not goals:
            response = "No savings goals set yet. Set one on the Goals page to plan for the future!"
        else:
            goal_info = [f"{desc}: ${current:.2f} of ${target:.2f} by {deadline}" for desc, target, current, deadline in goals]
            response = f"Your goals: {', '.join(goal_info)}. Need help reaching them?"
    elif re.search(patterns['reminder'], user_query):
        if 'set' in user_query or 'add' in user_query:
            task = re.search(r'(?:set|add)\s+(?:reminder|task)\s+(.+?)(?:\s+on\s+(.+))?$', user_query, re.IGNORECASE)
            if task:
                desc, date = task.groups()
                date = date if date else (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
                conn = sqlite3.connect('smartfinance.db')
                c = conn.cursor()
                c.execute('INSERT INTO reminders (user_id, description, date) VALUES (?, ?, ?)', (current_user.id, desc, date))
                conn.commit()
                conn.close()
                response = f"Reminder set for '{desc}' on {date}. Anything else?"
            else:
                response = "Please specify a task, e.g., 'set reminder to pay bills on 2025-07-10'."
        else:
            if not reminders:
                response = "No reminders set. Want to add one, like 'remind me to pay bills tomorrow'?"
            else:
                reminder_info = [f"{desc} on {date}" for desc, date in reminders]
                response = f"Your reminders: {', '.join(reminder_info)}. Need to add another?"
    elif re.search(patterns['weather'], user_query):
        response = mock_weather
    elif re.search(patterns['motivation'], user_query):
        response = f"Here's a motivational quote for you: '{random.choice(motivational_quotes)}' Keep shining, {current_user.username}!"
    elif re.search(patterns['joke'], user_query):
        response = f"Here's a joke: {random.choice(jokes)} Want another?"
    elif re.search(patterns['advice'], user_query):
        if 'finance' in user_query or 'money' in user_query:
            response = "\n".join(get_savings_tips(df, budgets))
        else:
            response = "Try to plan your day with a to-do list to stay productive. For financial advice, ask about budgets or savings!"
    elif re.search(patterns['balance'], user_query):
        income, expenses = get_monthly_summary(df)
        balance = income - expenses
        response = f"This month, your income is ${income:.2f}, expenses are ${expenses:.2f}, leaving a balance of ${balance:.2f}."
    elif re.search(patterns['savings_tip'], user_query):
        response = "\n".join(get_savings_tips(df, budgets))
    elif re.search(patterns['daily_tip'], user_query):
        response = "Start your day with a 5-minute plan: list 3 priorities and tackle them first. Also, drink water and take short breaks to stay energized!"
    elif re.search(patterns['time'], user_query):
        current_time = datetime.now().strftime('%I:%M %p')
        response = f"The current time is {current_time}. What's next on your schedule, {current_user.username}?"
    else:
        response = f"Sorry, {current_user.username}, I'm not sure how to help with that. Try asking about your finances, daily tasks, or something fun like a joke!"

    return jsonify({'response': response})

# Admin Routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT id, username, first_name, last_name, email FROM users WHERE is_admin = 0')
    users = c.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', users=users)

@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_details(user_id):
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('SELECT username, first_name, last_name, email FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    c.execute('SELECT id, type, category, amount, date FROM transactions WHERE user_id = ?', (user_id,))
    transactions = c.fetchall()
    c.execute('SELECT id, category, amount FROM budgets WHERE user_id = ?', (user_id,))
    budgets = c.fetchall()
    c.execute('SELECT id, description, target_amount, current_amount, deadline FROM goals WHERE user_id = ?', (user_id,))
    goals = c.fetchall()
    c.execute('SELECT id, description, date FROM reminders WHERE user_id = ?', (user_id,))
    reminders = c.fetchall()
    conn.close()
    return render_template('admin_user_details.html', user=user, transactions=transactions, budgets=budgets, goals=goals, reminders=reminders)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.')
        return redirect(url_for('admin_dashboard'))
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('DELETE FROM transactions WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM budgets WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM goals WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM reminders WHERE user_id = ?', (user_id,))
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('User and associated data deleted successfully.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_transaction/<int:transaction_id>', methods=['POST'])
@admin_required
def delete_transaction(transaction_id):
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()
    flash('Transaction deleted successfully.')
    return redirect(request.referrer)

@app.route('/admin/edit_budget/<int:budget_id>', methods=['POST'])
@admin_required
def admin_edit_budget(budget_id):  # Renamed to avoid conflict
    category = request.form['category']
    amount = float(request.form['amount'])
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('UPDATE budgets SET category = ?, amount = ? WHERE id = ?', (category, amount, budget_id))
    conn.commit()
    conn.close()
    flash('Budget updated successfully.')
    return redirect(request.referrer)

@app.route('/admin/delete_budget/<int:budget_id>', methods=['POST'])
@admin_required
def delete_budget(budget_id):
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('DELETE FROM budgets WHERE id = ?', (budget_id,))
    conn.commit()
    conn.close()
    flash('Budget deleted successfully.')
    return redirect(request.referrer)

@app.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@admin_required
def reset_password(user_id):
    new_password = secrets.token_urlsafe(12)
    password_hash = generate_password_hash(new_password)
    conn = sqlite3.connect('smartfinance.db')
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE id = ?', (password_hash, user_id))
    conn.commit()
    conn.close()
    flash(f'Password reset successfully. New password: {new_password}')
    return redirect(request.referrer)

if __name__ == '__main__':
    app.run(debug=True)