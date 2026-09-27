from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from collections import defaultdict
import json, os, hashlib, secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ─────────────────────────── MODELS ───────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    currency = db.Column(db.String(10), default='INR')
    monthly_income = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    goals = db.relationship('Goal', backref='user', lazy=True, cascade='all, delete-orphan')
    recurring = db.relationship('Recurring', backref='user', lazy=True, cascade='all, delete-orphan')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # income / expense
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    tags = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    limit_amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    saved_amount = db.Column(db.Float, default=0)
    deadline = db.Column(db.Date)
    icon = db.Column(db.String(10), default='🎯')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recurring(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # monthly/weekly/yearly
    next_date = db.Column(db.Date, nullable=False)
    active = db.Column(db.Boolean, default=True)

# ─────────────────────────── HELPERS ───────────────────────────

def hash_password(pw): return hashlib.sha256(pw.encode()).hexdigest()

def current_user():
    if 'user_id' not in session: return None
    return User.query.get(session['user_id'])

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

EXPENSE_CATEGORIES = ['Food & Dining','Transport','Shopping','Entertainment','Health','Education','Utilities','Housing','Travel','Insurance','Savings','Other']
INCOME_CATEGORIES = ['Salary','Freelance','Business','Investment','Gift','Rental','Other']

# ─────────────────────────── AUTH ───────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or request.form
        user = User.query.filter_by(username=data.get('username')).first()
        if user and user.password_hash == hash_password(data.get('password','')):
            session['user_id'] = user.id
            return jsonify({'success': True}) if request.is_json else redirect(url_for('dashboard'))
        return jsonify({'success': False, 'error': 'Invalid credentials'}) if request.is_json else render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() or request.form
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'success': False, 'error': 'Username taken'}) if request.is_json else render_template('register.html', error='Username taken')
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=hash_password(data.get('password','')),
            monthly_income=float(data.get('monthly_income', 0))
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return jsonify({'success': True}) if request.is_json else redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────── PAGES ───────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    now = datetime.utcnow()
    # This month stats
    txns = Transaction.query.filter_by(user_id=user.id).filter(
        db.extract('month', Transaction.date) == now.month,
        db.extract('year', Transaction.date) == now.year
    ).all()
    income = sum(t.amount for t in txns if t.type == 'income')
    expense = sum(t.amount for t in txns if t.type == 'expense')
    recent = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).limit(8).all()
    goals = Goal.query.filter_by(user_id=user.id).all()
    budgets = Budget.query.filter_by(user_id=user.id, month=now.month, year=now.year).all()
    return render_template('dashboard.html', user=user, income=income, expense=expense,
                           balance=income-expense, recent=recent, goals=goals, budgets=budgets, now=now)

@app.route('/transactions')
@login_required
def transactions():
    user = current_user()
    return render_template('transactions.html', user=user,
                           expense_cats=EXPENSE_CATEGORIES, income_cats=INCOME_CATEGORIES)

@app.route('/analytics')
@login_required
def analytics():
    user = current_user()
    return render_template('analytics.html', user=user)

@app.route('/budgets')
@login_required
def budgets():
    user = current_user()
    now = datetime.utcnow()
    buds = Budget.query.filter_by(user_id=user.id, month=now.month, year=now.year).all()
    return render_template('budgets.html', user=user, budgets=buds,
                           categories=EXPENSE_CATEGORIES, now=now)

@app.route('/goals')
@login_required
def goals():
    user = current_user()
    gs = Goal.query.filter_by(user_id=user.id).all()
    return render_template('goals.html', user=user, goals=gs)

@app.route('/recurring')
@login_required
def recurring():
    user = current_user()
    recs = Recurring.query.filter_by(user_id=user.id).all()
    return render_template('recurring.html', user=user, recurring=recs,
                           expense_cats=EXPENSE_CATEGORIES, income_cats=INCOME_CATEGORIES)

@app.route('/settings')
@login_required
def settings():
    user = current_user()
    return render_template('settings.html', user=user)

# ─────────────────────────── API: TRANSACTIONS ───────────────────────────

@app.route('/api/transactions', methods=['GET'])
@login_required
def api_get_transactions():
    user = current_user()
    q = Transaction.query.filter_by(user_id=user.id)
    if request.args.get('type'): q = q.filter_by(type=request.args['type'])
    if request.args.get('category'): q = q.filter_by(category=request.args['category'])
    if request.args.get('month'):
        m,y = int(request.args['month']), int(request.args.get('year', datetime.utcnow().year))
        q = q.filter(db.extract('month', Transaction.date)==m, db.extract('year', Transaction.date)==y)
    if request.args.get('search'):
        s = f"%{request.args['search']}%"
        q = q.filter(Transaction.description.ilike(s) | Transaction.category.ilike(s))
    txns = q.order_by(Transaction.date.desc()).all()
    return jsonify([{
        'id': t.id, 'type': t.type, 'amount': t.amount, 'category': t.category,
        'description': t.description, 'date': t.date.isoformat(), 'tags': t.tags
    } for t in txns])

@app.route('/api/transactions', methods=['POST'])
@login_required
def api_add_transaction():
    user = current_user()
    d = request.get_json()
    t = Transaction(
        user_id=user.id,
        type=d['type'],
        amount=float(d['amount']),
        category=d['category'],
        description=d.get('description',''),
        date=datetime.strptime(d['date'], '%Y-%m-%d').date(),
        tags=d.get('tags','')
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({'success': True, 'id': t.id})

@app.route('/api/transactions/<int:tid>', methods=['DELETE'])
@login_required
def api_delete_transaction(tid):
    user = current_user()
    t = Transaction.query.filter_by(id=tid, user_id=user.id).first_or_404()
    db.session.delete(t)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/transactions/<int:tid>', methods=['PUT'])
@login_required
def api_update_transaction(tid):
    user = current_user()
    t = Transaction.query.filter_by(id=tid, user_id=user.id).first_or_404()
    d = request.get_json()
    t.amount = float(d.get('amount', t.amount))
    t.category = d.get('category', t.category)
    t.description = d.get('description', t.description)
    t.date = datetime.strptime(d['date'], '%Y-%m-%d').date() if 'date' in d else t.date
    t.tags = d.get('tags', t.tags)
    db.session.commit()
    return jsonify({'success': True})

# ─────────────────────────── API: ANALYTICS ───────────────────────────

@app.route('/api/analytics/overview')
@login_required
def api_analytics_overview():
    user = current_user()
    now = datetime.utcnow()
    months_data = []
    for i in range(6):
        dt = now - timedelta(days=30*i)
        txns = Transaction.query.filter_by(user_id=user.id).filter(
            db.extract('month', Transaction.date)==dt.month,
            db.extract('year', Transaction.date)==dt.year
        ).all()
        months_data.append({
            'month': dt.strftime('%b %Y'),
            'income': round(sum(t.amount for t in txns if t.type=='income'), 2),
            'expense': round(sum(t.amount for t in txns if t.type=='expense'), 2)
        })
    months_data.reverse()

    # Category breakdown this month
    txns_month = Transaction.query.filter_by(user_id=user.id, type='expense').filter(
        db.extract('month', Transaction.date)==now.month,
        db.extract('year', Transaction.date)==now.year
    ).all()
    cat_map = defaultdict(float)
    for t in txns_month:
        cat_map[t.category] += t.amount

    # Daily spending last 30 days
    daily = defaultdict(float)
    start = now.date() - timedelta(days=29)
    txns_30 = Transaction.query.filter_by(user_id=user.id, type='expense').filter(
        Transaction.date >= start
    ).all()
    for t in txns_30:
        daily[t.date.isoformat()] += t.amount
    daily_list = []
    for i in range(30):
        d = (start + timedelta(days=i)).isoformat()
        daily_list.append({'date': d, 'amount': round(daily.get(d, 0), 2)})

    return jsonify({
        'monthly': months_data,
        'categories': [{'category': k, 'amount': round(v,2)} for k,v in sorted(cat_map.items(), key=lambda x: -x[1])],
        'daily': daily_list
    })

@app.route('/api/analytics/insights')
@login_required
def api_analytics_insights():
    user = current_user()
    now = datetime.utcnow()
    # This vs last month
    this_txns = Transaction.query.filter_by(user_id=user.id).filter(
        db.extract('month', Transaction.date)==now.month,
        db.extract('year', Transaction.date)==now.year
    ).all()
    last = now - timedelta(days=30)
    last_txns = Transaction.query.filter_by(user_id=user.id).filter(
        db.extract('month', Transaction.date)==last.month,
        db.extract('year', Transaction.date)==last.year
    ).all()
    this_exp = sum(t.amount for t in this_txns if t.type=='expense')
    last_exp = sum(t.amount for t in last_txns if t.type=='expense')
    this_inc = sum(t.amount for t in this_txns if t.type=='income')
    savings_rate = round((this_inc - this_exp)/this_inc*100, 1) if this_inc > 0 else 0
    change = round(((this_exp - last_exp)/last_exp*100), 1) if last_exp > 0 else 0
    top_cats = defaultdict(float)
    for t in this_txns:
        if t.type == 'expense':
            top_cats[t.category] += t.amount
    top = sorted(top_cats.items(), key=lambda x: -x[1])[:3]
    return jsonify({
        'this_month_expense': round(this_exp, 2),
        'last_month_expense': round(last_exp, 2),
        'expense_change_pct': change,
        'savings_rate': savings_rate,
        'top_categories': [{'category': k, 'amount': round(v,2)} for k,v in top],
        'transaction_count': len(this_txns)
    })

# ─────────────────────────── API: BUDGETS ───────────────────────────

@app.route('/api/budgets', methods=['GET'])
@login_required
def api_get_budgets():
    user = current_user()
    now = datetime.utcnow()
    m = int(request.args.get('month', now.month))
    y = int(request.args.get('year', now.year))
    buds = Budget.query.filter_by(user_id=user.id, month=m, year=y).all()
    result = []
    for b in buds:
        spent = db.session.query(db.func.sum(Transaction.amount)).filter_by(
            user_id=user.id, category=b.category, type='expense'
        ).filter(db.extract('month', Transaction.date)==m, db.extract('year', Transaction.date)==y).scalar() or 0
        result.append({'id': b.id, 'category': b.category, 'limit': b.limit_amount, 'spent': round(spent,2)})
    return jsonify(result)

@app.route('/api/budgets', methods=['POST'])
@login_required
def api_add_budget():
    user = current_user()
    d = request.get_json()
    now = datetime.utcnow()
    existing = Budget.query.filter_by(user_id=user.id, category=d['category'],
                                       month=int(d.get('month', now.month)), year=int(d.get('year', now.year))).first()
    if existing:
        existing.limit_amount = float(d['limit'])
    else:
        b = Budget(user_id=user.id, category=d['category'], limit_amount=float(d['limit']),
                   month=int(d.get('month', now.month)), year=int(d.get('year', now.year)))
        db.session.add(b)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/budgets/<int:bid>', methods=['DELETE'])
@login_required
def api_delete_budget(bid):
    user = current_user()
    b = Budget.query.filter_by(id=bid, user_id=user.id).first_or_404()
    db.session.delete(b)
    db.session.commit()
    return jsonify({'success': True})

# ─────────────────────────── API: GOALS ───────────────────────────

@app.route('/api/goals', methods=['POST'])
@login_required
def api_add_goal():
    user = current_user()
    d = request.get_json()
    g = Goal(user_id=user.id, name=d['name'], target_amount=float(d['target']),
             saved_amount=float(d.get('saved', 0)), icon=d.get('icon','🎯'),
             deadline=datetime.strptime(d['deadline'], '%Y-%m-%d').date() if d.get('deadline') else None)
    db.session.add(g)
    db.session.commit()
    return jsonify({'success': True, 'id': g.id})

@app.route('/api/goals/<int:gid>', methods=['PUT'])
@login_required
def api_update_goal(gid):
    user = current_user()
    g = Goal.query.filter_by(id=gid, user_id=user.id).first_or_404()
    d = request.get_json()
    if 'saved' in d: g.saved_amount = float(d['saved'])
    if 'name' in d: g.name = d['name']
    if 'target' in d: g.target_amount = float(d['target'])
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/goals/<int:gid>', methods=['DELETE'])
@login_required
def api_delete_goal(gid):
    user = current_user()
    g = Goal.query.filter_by(id=gid, user_id=user.id).first_or_404()
    db.session.delete(g)
    db.session.commit()
    return jsonify({'success': True})

# ─────────────────────────── API: RECURRING ───────────────────────────

@app.route('/api/recurring', methods=['POST'])
@login_required
def api_add_recurring():
    user = current_user()
    d = request.get_json()
    r = Recurring(user_id=user.id, name=d['name'], amount=float(d['amount']),
                  type=d['type'], category=d['category'], frequency=d['frequency'],
                  next_date=datetime.strptime(d['next_date'], '%Y-%m-%d').date())
    db.session.add(r)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/recurring/<int:rid>', methods=['DELETE'])
@login_required
def api_delete_recurring(rid):
    user = current_user()
    r = Recurring.query.filter_by(id=rid, user_id=user.id).first_or_404()
    db.session.delete(r)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/recurring/<int:rid>/toggle', methods=['POST'])
@login_required
def api_toggle_recurring(rid):
    user = current_user()
    r = Recurring.query.filter_by(id=rid, user_id=user.id).first_or_404()
    r.active = not r.active
    db.session.commit()
    return jsonify({'success': True, 'active': r.active})

# ─────────────────────────── API: SETTINGS ───────────────────────────

@app.route('/api/settings', methods=['POST'])
@login_required
def api_update_settings():
    user = current_user()
    d = request.get_json()
    if 'monthly_income' in d: user.monthly_income = float(d['monthly_income'])
    if 'currency' in d: user.currency = d['currency']
    if 'email' in d: user.email = d['email']
    if d.get('new_password') and d.get('current_password'):
        if user.password_hash == hash_password(d['current_password']):
            user.password_hash = hash_password(d['new_password'])
        else:
            return jsonify({'success': False, 'error': 'Wrong current password'})
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/export')
@login_required
def api_export():
    user = current_user()
    txns = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date','Type','Category','Amount','Description','Tags'])
    for t in txns:
        writer.writerow([t.date, t.type, t.category, t.amount, t.description, t.tags])
    from flask import Response
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=transactions.csv'})

# ─────────────────────────── SEED DEMO DATA ───────────────────────────

def seed_demo(user_id):
    import random
    now = datetime.utcnow()
    cats_exp = ['Food & Dining','Transport','Shopping','Entertainment','Health','Utilities','Housing']
    for i in range(45):
        d = now.date() - timedelta(days=random.randint(0, 89))
        db.session.add(Transaction(user_id=user_id, type='expense',
            amount=round(random.uniform(100, 8000), 2),
            category=random.choice(cats_exp), description=f'Sample expense {i+1}', date=d))
    for i in range(6):
        d = now.date() - timedelta(days=i*15)
        db.session.add(Transaction(user_id=user_id, type='income',
            amount=round(random.uniform(30000, 80000), 2),
            category='Salary', description='Monthly salary', date=d))
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='demo').first():
            demo = User(username='demo', email='demo@example.com',
                        password_hash=hashlib.sha256(b'demo123').hexdigest(),
                        monthly_income=75000, currency='INR')
            db.session.add(demo)
            db.session.commit()
            seed_demo(demo.id)
            now = datetime.utcnow()
            # Add sample goals
            db.session.add(Goal(user_id=demo.id, name='Emergency Fund', target_amount=300000, saved_amount=125000, icon='🏦'))
            db.session.add(Goal(user_id=demo.id, name='New Laptop', target_amount=80000, saved_amount=45000, icon='💻'))
            db.session.add(Goal(user_id=demo.id, name='Vacation', target_amount=150000, saved_amount=30000, icon='✈️'))
            # Sample budgets
            db.session.add(Budget(user_id=demo.id, category='Food & Dining', limit_amount=12000, month=now.month, year=now.year))
            db.session.add(Budget(user_id=demo.id, category='Transport', limit_amount=5000, month=now.month, year=now.year))
            db.session.add(Budget(user_id=demo.id, category='Shopping', limit_amount=10000, month=now.month, year=now.year))
            db.session.add(Budget(user_id=demo.id, category='Entertainment', limit_amount=4000, month=now.month, year=now.year))
            # Recurring
            db.session.add(Recurring(user_id=demo.id, name='Netflix', amount=649, type='expense',
                category='Entertainment', frequency='monthly', next_date=(now+timedelta(days=5)).date()))
            db.session.add(Recurring(user_id=demo.id, name='Gym', amount=1500, type='expense',
                category='Health', frequency='monthly', next_date=(now+timedelta(days=10)).date()))
            db.session.commit()
    app.run(debug=True, port=5000)
