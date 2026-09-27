# ◈ FinanceOS — Personal Finance Tracker

A full-stack personal finance web application built with **Python Flask**, **SQLite**, and **vanilla HTML/CSS/JS**.

---

## Features

| Feature | Details |
|---|---|
| **Dashboard** | Net balance, monthly income/expense, budget progress, goals summary, 6-month chart |
| **Transactions** | Add, filter, search, delete — with type, category, date, tags |
| **Analytics** | Monthly trends, category doughnut, daily spending, savings bar chart, AI insights |
| **Budgets** | Set per-category monthly limits with visual progress and overspend alerts |
| **Savings Goals** | Track goals with icon, target, saved amount, deadline and progress |
| **Recurring** | Manage subscriptions, EMIs, salary — toggle active/paused |
| **Settings** | Update profile, income, currency, password |
| **CSV Export** | One-click export of all transactions |
| **Auth** | User registration + login with session management |
| **Demo Account** | Pre-seeded with 3 months of data |

---

## Tech Stack

- **Backend**: Python 3, Flask, Flask-SQLAlchemy
- **Database**: SQLite (file-based, zero config)
- **Frontend**: HTML5, CSS3 (custom dark theme), Vanilla JS
- **Charts**: Chart.js 4.4
- **Fonts**: Syne + DM Sans (Google Fonts)

---

## Quick Start

### 1. Install dependencies
```bash
cd finance_tracker
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://localhost:5000
```

### 4. Demo login
- **Username**: `demo`
- **Password**: `demo123`

---

## Project Structure

```
finance_tracker/
├── app.py                    # Flask app + all routes + DB models
├── requirements.txt
├── finance.db                # SQLite DB (auto-created)
├── static/
│   ├── css/style.css         # Full dark theme + all components
│   └── js/app.js             # Shared utilities + chart helpers
└── templates/
    ├── base.html             # Sidebar layout shell
    ├── login.html
    ├── register.html
    ├── dashboard.html        # Overview + quick-add
    ├── transactions.html     # Full transaction management
    ├── analytics.html        # 4 charts + insights
    ├── budgets.html          # Budget cards with progress
    ├── goals.html            # Goal cards with add-money modal
    ├── recurring.html        # Recurring transaction manager
    └── settings.html         # User preferences
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions` | List with filters (type, category, month, search) |
| POST | `/api/transactions` | Add transaction |
| PUT | `/api/transactions/<id>` | Update transaction |
| DELETE | `/api/transactions/<id>` | Delete transaction |
| GET | `/api/analytics/overview` | Monthly trends, category breakdown, daily |
| GET | `/api/analytics/insights` | Savings rate, change vs last month |
| GET/POST | `/api/budgets` | Get/set budgets (with spent calc) |
| DELETE | `/api/budgets/<id>` | Remove budget |
| POST | `/api/goals` | Create savings goal |
| PUT | `/api/goals/<id>` | Update goal (add money) |
| DELETE | `/api/goals/<id>` | Delete goal |
| POST | `/api/recurring` | Add recurring transaction |
| DELETE | `/api/recurring/<id>` | Remove recurring |
| POST | `/api/recurring/<id>/toggle` | Toggle active/paused |
| POST | `/api/settings` | Update user settings |
| GET | `/api/export` | Download transactions as CSV |
