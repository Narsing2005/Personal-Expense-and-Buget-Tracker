# Finora — Personal Expense & Budget Tracker

[![Tests](https://img.shields.io/badge/pytest-16%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.1-black.svg)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/react-18.2-61dafb.svg)](https://react.dev/)
[![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo-green.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Finora** is a complete, modern, responsive full-stack personal finance web application built with **React.js**, **Python Flask REST APIs**, **MongoDB**, **Flask-JWT-Extended**, and **Chart.js**. It empowers users to monitor personal cash flow, record income and expenses, define monthly category budgets, analyze multi-period financial trends, and receive automated 4-tier spending notifications.

---

## 🌟 Key Application Features

### 1. User Authentication & Security
* **JWT-Based Authentication:** Stateless JSON Web Token authentication with `@jwt_required()` route protection.
* **Bcrypt Password Hashing:** Industry-standard salted password encryption.
* **Strict Tenant Isolation:** Every transaction, budget, and alert is strictly scoped to the authenticated user ID.
* **Preloaded Demo Mode:** Instant one-click exploration with Alex Morgan (`alex@finora.io` / `Finora2026!`).

### 2. Financial Dashboard
* **Dynamic KPI Cards:** Total Income, Total Expenses, Current Net Balance, and Monthly Savings & Savings Rate.
* **Budget Utilization Banner:** Real-time visual progress bar showing overall monthly budget consumption.
* **Interactive Chart.js Visualizations:**
  1. **Income vs. Expense Bar Chart:** 6-month comparative cash flow.
  2. **Category Expense Doughnut Chart:** Breakdown by category with percentage share.
  3. **Monthly Spending Line Chart:** Spending velocity over time.
* **Recent Transactions:** Quick summary of latest 5 ledger entries.

### 3. Transaction Management
* **Full CRUD Operations:** Add, edit, delete, and view income and expense transactions.
* **Comprehensive Fields:** ID, Title, Amount, Type (`Income` or `Expense`), Category, Date (`YYYY-MM-DD`), and Description.
* **Live Search & Filtering:** Filter simultaneously by keyword, category, transaction type, or date range.

### 4. Monthly Budget Planner
* **Category Limits:** Set monthly spending targets for categories (e.g., Food & Dining, Rent, Utilities, Entertainment).
* **Real-time Spending Tracking:** Automatically aggregates transactions for the active month against set limits.
* **Utilization Percentages:** Computes exact spent amount, remaining balance, and utilization percentage.
* **Color-Coded Progress Bars:**
  - 🟢 **< 50%:** Safe / On Track
  - 🔵 **50% - 79%:** Informational Notice
  - 🟠 **80% - 99%:** Warning
  - 🔴 **>= 100%:** Limit Reached / Overspent

### 5. Automated 4-Tier Budget Alert Engine
Finora automatically recalculates and registers alert notifications whenever expenses are added or modified:
* ℹ️ **50% Utilization:** Informational notification alerting that half of the budget is spent.
* ⚠️ **80% Utilization:** Warning notification prompting caution.
* 🚨 **100% Utilization:** Notification indicating budget limit has been reached.
* 🛑 **> 100% Utilization:** Urgent overspending notification displaying excess dollar amount and percentage.
* **Alerts Notification Center:** Accessible via the top-navigation bell icon with unread badge counter, mark as read, and clear all.

### 6. Reports & Analytics
* **Annual Monthly Performance:** Full 12-month breakdown of income, expenses, net savings, and savings rate.
* **Category-Wise Distribution:** Breakdown with total spent, percentage share, transaction count, average per transaction, and peak expense.
* **Daily Spending Log:** Date-by-date summary of cash flow.
* **Date Range Filtering:** Custom date range selection.

---

## 🎨 UI/UX Design System

* **Primary Color:** Navy Blue (`#0f172a`, `#1e293b`)
* **Secondary Color:** Teal (`#0d9488`, `#14b8a6`)
* **Background:** Light Gray (`#f8fafc`)
* **Cards:** Pure White (`#ffffff`) with subtle elevations
* **Warning:** Amber Orange (`#f59e0b`)
* **Danger:** Coral Red (`#ef4444`)
* **Success:** Emerald Green (`#10b981`)
* **Responsive Layout:** Adaptive sidebar for desktop, tablet, and mobile with slide-out drawer.

---

## 📂 Project Architecture

```
Finora/
├── app.py                     # Main Flask Application Server & Blueprint Registry
├── config.py                  # App configuration & environment settings
├── database.py                # PyMongo connection manager & mongomock fallback
├── seed_data.py               # Preloaded demo financial data seeder
├── requirements.txt           # Python backend dependencies
├── pytest.ini                 # Pytest configuration                                          `
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # Comprehensive user & developer guide
├── routes/                    # RESTful API Blueprints
│   ├── auth_routes.py         # /api/auth (register, login, logout, me)
│   ├── transaction_routes.py  # /api/transactions (CRUD, search, filter)
│   ├── budget_routes.py       # /api/budgets (CRUD, utilization calculation)
│   ├── dashboard_routes.py    # /api/dashboard (summary KPIs, analytics charts)
│   ├── report_routes.py       # /api/reports (monthly, category, summary)
│   └── notification_routes.py # /api/notifications (budget alerts, read/clear)
├── utils/                     # Utility Modules
│   ├── auth_helpers.py        # Bcrypt hashing & doc serialization
│   ├── validators.py          # Input schemas and validation logic
│   └── budget_calculator.py   # 4-tier alert trigger engine
├── tests/                     # Automated Test Suite (Pytest)
│   ├── conftest.py            # App fixtures & authenticated client headers
│   ├── test_auth.py           # Registration & login tests
│   ├── test_transactions.py   # Transaction CRUD tests
│   ├── test_budgets.py        # Budget calculations & 4-tier alert tests
│   └── test_reports.py        # Summary, analytics, & report tests
├── templates/
│   └── index.html             # React SPA container
└── static/
    ├── css/style.css          # Finora custom design system
    └── js/app.js              # Complete React application & Chart.js integration
```

---

## 🛠️ Database Design (MongoDB Collections)

1. **`users` Collection**
   * `_id`: ObjectId
   * `name`: String
   * `email`: String (Unique index)
   * `password_hash`: String (Bcrypt salted hash)
   * `currency`: String (Default "USD")
   * `created_at`: Datetime

2. **`transactions` Collection**
   * `_id`: ObjectId
   * `user_id`: String (Indexed)
   * `title`: String
   * `amount`: Float (> 0)
   * `type`: String (`Income` or `Expense`)
   * `category`: String
   * `date`: String (`YYYY-MM-DD`, Indexed)
   * `description`: String
   * `created_at`: Datetime

3. **`budgets` Collection**
   * `_id`: ObjectId
   * `user_id`: String (Indexed)
   * `month`: String (`YYYY-MM`, Indexed)
   * `category`: String
   * `limit_amount`: Float (> 0)
   * `notes`: String
   * `created_at`: Datetime

4. **`notifications` Collection**
   * `_id`: ObjectId
   * `user_id`: String (Indexed)
   * `category`: String
   * `month`: String (`YYYY-MM`)
   * `threshold`: Integer (`50`, `80`, `100`, `105`)
   * `level`: String (`info`, `warning`, `danger`)
   * `title`: String
   * `message`: String
   * `spent`: Float
   * `limit_amount`: Float
   * `percentage`: Float
   * `read`: Boolean
   * `created_at`: Datetime

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+
* (Optional) MongoDB 6.0+ 

### 2. Setup & Installation

Clone or open the project folder:
```bash
cd Finora
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Application

Start the Flask server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://localhost:5000
```

### 4. Instant Demo Mode
Click the **"Explore with Preloaded Demo Account"** button on the login screen to instantly log into the pre-populated account (`alex@finora.io` / `Finora2026!`) loaded with realistic transactions, active budgets, and triggered alerts!

---

## 🧪 Running Automated Tests

Run the full Pytest test suite:
```bash
pytest
```


## 📡 REST API Reference

| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/register` | Register new user account | No |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT access token | No |
| `POST` | `/api/auth/logout` | Terminate session | No |
| `GET` | `/api/auth/me` | Fetch authenticated user profile | Yes |
| `GET` | `/api/transactions` | Query transactions (filters: search, type, category, date) | Yes |
| `POST` | `/api/transactions` | Create new income or expense transaction | Yes |
| `PUT` | `/api/transactions/<id>` | Update existing transaction | Yes |
| `DELETE`| `/api/transactions/<id>` | Delete transaction | Yes |
| `GET` | `/api/budgets` | Get category budgets and utilization for a month | Yes |
| `POST` | `/api/budgets` | Define a new category budget limit | Yes |
| `PUT` | `/api/budgets/<id>` | Modify budget limit or notes | Yes |
| `DELETE`| `/api/budgets/<id>` | Remove budget limit | Yes |
| `GET` | `/api/dashboard/summary` | Fetch executive KPI card metrics & recent transactions | Yes |
| `GET` | `/api/dashboard/analytics`| Fetch 3 chart datasets (bar, pie, line) | Yes |
| `GET` | `/api/reports/monthly` | Annual 12-month performance breakdown | Yes |
| `GET` | `/api/reports/category` | Category-wise expense share and statistics | Yes |
| `GET` | `/api/reports/summary` | Daily spending summary log with date range | Yes |
| `GET` | `/api/notifications` | Fetch budget threshold alerts & unread counter | Yes |
| `POST` | `/api/notifications/<id>/read` | Mark individual notification as read | Yes |
| `POST` | `/api/notifications/clear` | Mark all notifications as read | Yes |

---

## 📄 License
This project is licensed under the MIT License.
