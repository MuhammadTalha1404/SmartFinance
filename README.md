# Smart Finance

Smart Finance is a personal finance management web application built with Flask. It helps users manage income, expenses, budgets, savings goals, reminders, and financial reports from one simple dashboard.

The project also includes a basic finance chatbot, spending prediction, tax estimation, PDF report export, profile management, and an admin panel for managing users and their financial data.

## Features

* User registration and login
* Secure password hashing
* User dashboard
* Income and expense tracking
* Add and edit transactions
* Category-wise spending chart
* Budget management
* Savings goal tracking
* Reminder/task management
* User profile management
* Profile picture upload
* Weekly, monthly, and yearly PDF report export
* Spending prediction using Linear Regression
* Basic tax estimation
* Built-in finance chatbot
* Admin dashboard
* Admin user management
* Admin transaction and budget management
* Admin password reset feature

## Tech Stack

* Python
* Flask
* Flask-Login
* SQLite
* Pandas
* NumPy
* Matplotlib
* Scikit-learn
* ReportLab
* HTML
* CSS
* JavaScript

## Project Purpose

The main purpose of Smart Finance is to help users manage their personal finances in a simple and practical way.

Users can record their income and expenses, set budgets, create financial goals, view spending summaries, and export financial reports. The system also provides basic financial insights using charts and simple machine learning prediction.

## Main Modules

## Authentication

Smart Finance includes a complete authentication system.

Users can:

* Register an account
* Log in securely
* Log out
* Access protected pages only after login

Passwords are hashed before being stored in the database.

## Dashboard

The dashboard gives users a quick financial overview.

It shows:

* Total income
* Total expenses
* Current balance
* Recent transactions
* Spending by category

A pie chart is generated to show how the user's expenses are divided across different categories.

## Transactions

Users can add and manage income and expense records.

Each transaction includes:

* Type
* Category
* Amount
* Date

Users can also edit existing transactions.

## Budgets

The budget module allows users to set category-based budgets.

This helps users track spending limits and manage their money more responsibly.

## Goals

Users can create financial goals.

Each goal includes:

* Description
* Target amount
* Current amount
* Deadline

This feature helps users plan savings and track progress toward financial targets.

## Reminders

Users can create reminders for important tasks.

Examples include:

* Paying bills
* Saving money
* Checking monthly expenses
* Completing financial tasks

## Reports

The reports module provides useful financial tools.

Users can:

* Predict future spending
* Estimate tax
* Export financial reports as PDF

Reports can be generated for:

* Weekly period
* Monthly period
* Yearly period

## Spending Prediction

Smart Finance uses Linear Regression to predict future spending.

The prediction is based on previous expense records. The system requires at least two expense records before it can generate a prediction.

## Tax Estimation

The project includes a simple tax estimation feature.

It calculates estimated tax based on the user's recorded income using a fixed tax rate.

## PDF Export

Users can export financial reports as PDF files.

The reports include transaction details such as:

* Date
* Type
* Category
* Amount

PDF files are generated using ReportLab.

## Chatbot

Smart Finance includes a basic chatbot that can respond to user queries.

The chatbot can answer questions related to:

* Spending
* Budgets
* Goals
* Reminders
* Balance
* Savings tips
* Motivation
* Jokes
* Time

It uses simple keyword and pattern matching to understand the user's query.

## Profile Management

Users can update their profile information.

Profile details include:

* Age
* Occupation
* Income
* Location
* Financial goals summary
* Profile picture

Uploaded profile pictures are stored in the `static/uploads` folder.

## Admin Panel

Smart Finance includes an admin dashboard.

The admin can:

* View all registered users
* View user financial details
* Delete users
* Delete transactions
* Edit budgets
* Delete budgets
* Reset user passwords

## Default Admin Account

The application creates a default admin account automatically.

```text
Username: admin
Password: Admin@1234
```

Important: Change the default admin password before deploying the project.

## Installation

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/smart-finance.git
cd smart-finance
```

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

## 3. Activate the Virtual Environment

For Windows:

```bash
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

## 4. Install Required Packages

```bash
pip install flask flask-login werkzeug matplotlib reportlab pandas scikit-learn numpy
```

Or install from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Requirements File

Create a `requirements.txt` file and add:

```text
Flask
Flask-Login
Werkzeug
matplotlib
reportlab
pandas
scikit-learn
numpy
```

## Run the Project

```bash
python main.py
```

After running the project, open this URL in your browser:

```text
http://127.0.0.1:5000
```

## Database

Smart Finance uses SQLite as the database.

When the application runs for the first time, it automatically creates a database file:

```text
smartfinance.db
```

The database includes the following tables:

* Users
* Transactions
* Budgets
* Goals
* Reminders

## Folder Structure

```text
smart-finance/
│
├── main.py
├── smartfinance.db
├── requirements.txt
│
├── static/
│   ├── uploads/
│   └── spending_chart.png
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── transactions.html
│   ├── edit_transaction.html
│   ├── budgets.html
│   ├── edit_budget.html
│   ├── goals.html
│   ├── reminders.html
│   ├── reports.html
│   ├── profile.html
│   ├── chat.html
│   ├── admin_dashboard.html
│   └── admin_user_details.html
│
└── README.md
```

## Important Routes

| Route               | Description             |
| ------------------- | ----------------------- |
| `/`                 | Home page               |
| `/register`         | User registration       |
| `/login`            | User login              |
| `/logout`           | User logout             |
| `/dashboard`        | User dashboard          |
| `/transactions`     | View transactions       |
| `/add_transaction`  | Add transaction         |
| `/budgets`          | View budgets            |
| `/set_budget`       | Set budget              |
| `/goals`            | View goals              |
| `/set_goal`         | Set financial goal      |
| `/reminders`        | View reminders          |
| `/set_reminder`     | Set reminder            |
| `/reports`          | Reports page            |
| `/predict_spending` | Predict future spending |
| `/estimate_tax`     | Estimate tax            |
| `/profile`          | User profile            |
| `/chat`             | Chatbot page            |
| `/chat_process`     | Process chatbot message |
| `/admin`            | Admin dashboard         |

## Security Notes

Before deploying this project, make sure to:

* Change the Flask secret key
* Change the default admin password
* Do not run the app with `debug=True` in production
* Use environment variables for sensitive values
* Add stronger file upload validation
* Use a production database such as PostgreSQL or MySQL
* Add CSRF protection for forms
* Improve error handling

## Future Improvements

* Email verification
* Forgot password by email
* Better chatbot with AI integration
* Advanced financial analytics
* Monthly budget comparison
* Recurring transactions
* Investment tracking
* Better responsive design
* API endpoints
* Deployment on Render, Railway, or PythonAnywhere

## Learning Outcomes

Through this project, I practiced:

* Flask web development
* User authentication
* SQLite database handling
* CRUD operations
* Data visualization with Matplotlib
* Machine learning with Linear Regression
* PDF generation
* Admin panel development
* File uploads
* Basic chatbot logic
* Full-stack project structure

## Author

Muhammad Talha

## License

This project is created for educational and learning purposes.
