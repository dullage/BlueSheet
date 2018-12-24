#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from helpers import ordinal
from spending import calculations
from datetime import datetime, timedelta
from os import environ, path

# Basic brute force prevent, see User class.
if path.isfile("LOCK"):
    exit(1)

DATABASE_PATH = environ.get('DATABASE_PATH', 'BlueSheet.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'

CONFIGURATION_NAMES = [
    'month_start_date',
    'weekly_pay_day',
    'weekly_spending_amount'
]

app = Flask(__name__)

app.secret_key = b'bg31HxAIUmxAI'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)


# region Database
class User(db.Model):
    __tablename__ = "user"
    _failed_login_attempts = 0

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, username, password):
        self.id - id
        self.username = username
        self.password = password

    @classmethod
    def login(cls, username, password, session):
        user = User.query.filter_by(username=username).first()
        login_failure = False

        if user is None:
            login_failure = True
        elif user.password != password:
            login_failure = True

        if login_failure is True:
            # Basic brute force prevention.
            cls._failed_login_attempts = cls._failed_login_attempts + 1
            if cls._failed_login_attempts >= 10:
                open('LOCK', 'a').close()
                exit(1)
            else:
                return False
        else:
            session['username'] = user.username
            session['last_activity'] = \
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return user

    @classmethod
    def login_required(cls, session):
        if 'username' not in session:
            return True
        if 'last_activity' not in session:
            return True
        if datetime.strptime(session['last_activity'], '%Y-%m-%d %H:%M:%S') \
                < (datetime.now() - timedelta(minutes=10)):
            return True
        else:
            session['last_activity'] = \
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return False


class Configuration(db.Model):
    __tablename__ = "configuration"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    value = db.Column(db.String(255), nullable=False)

    def __init__(self, name, value):
        self.name = name
        self.value = value

    @classmethod
    def get(cls):
        configuration_data = Configuration.query.all()
        configuration = {}

        for entry in configuration_data:
            configuration[entry.name] = entry.value

            if entry.name == "month_start_date":
                configuration["month_start_date_ordinal"] = \
                    ordinal(int(entry.value))

        return configuration


class Salary(db.Model):
    __tablename__ = "salary"

    id = db.Column(db.Integer, primary_key=True)
    annual_gross_salary = db.Column(db.Numeric, nullable=False)
    annual_tax_allowance = db.Column(db.Numeric, nullable=False)
    tax_rate = db.Column(db.Numeric, nullable=False)
    annual_ni_allowance = db.Column(db.Numeric, nullable=False)
    ni_rate = db.Column(db.Numeric, nullable=False)
    annual_non_pensionable_value = db.Column(db.Numeric, nullable=False)
    pension_contribution = db.Column(db.Numeric, nullable=False)

    def __init__(
        self,
        annual_gross_salary,
        annual_tax_allowance,
        tax_rate,
        annual_ni_allowance,
        ni_rate,
        annual_non_pensionable_value,
        pension_contribution
    ):
        self.annual_gross_salary = annual_gross_salary
        self.annual_tax_allowance = annual_tax_allowance
        self.tax_rate = tax_rate
        self.annual_ni_allowance = annual_ni_allowance
        self.ni_rate = ni_rate
        self.annual_non_pensionable_value = annual_non_pensionable_value
        self.pension_contribution = pension_contribution

    @property
    def annual_tax(self):
        return (self.annual_gross_salary - self.annual_tax_allowance) \
            * (self.tax_rate / 100)

    @property
    def annual_ni(self):
        return (self.annual_gross_salary - self.annual_ni_allowance) \
            * (self.ni_rate / 100)

    @property
    def annual_pension(self):
        return (self.annual_gross_salary - self.annual_non_pensionable_value) \
            * (self.pension_contribution / 100)

    @property
    def annual_pension_tax_relief(self):
        return self.annual_pension \
            * (self.tax_rate / 100)

    @property
    def annual_net_salary(self):
        return self.annual_gross_salary \
            - self.annual_tax \
            - self.annual_ni \
            - self.annual_pension \
            + self.annual_pension_tax_relief


class Account(db.Model):
    __tablename__ = "account"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.String(8000))
    outgoings = db.relationship("Outgoing", backref="account", lazy=True)

    def __init__(self, name, notes=None):
        self.name = name
        self.notes = notes


class Outgoing(db.Model):
    __tablename__ = "outgoing"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Numeric, nullable=False)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey('account.id'),
        nullable=False
    )
    notes = db.Column(db.String(8000))

    def __init__(self, name, value, account_id, notes=None):
        self.name = name
        self.value = value
        self.account_id = account_id
        self.notes = notes

    @classmethod
    def total(cls):
        all_outgoings = cls.query.all()
        total_outgoings = 0
        for outgoing in all_outgoings:
            total_outgoings = total_outgoings + outgoing.value

        return total_outgoings


db.create_all()

# Initialise a Salary row
salary_count = Salary.query.count()
if salary_count == 0:
    db.session.add(Salary(1, 1, 1, 1, 1, 1, 1))
    db.session.commit()
# endregion


# region Login
@app.route("/login")
def login():
    message = request.args.get('message')
    return render_template(
        'login.html',
        message=message
    )


@app.route("/login-handler", methods=['post'])
def login_handler():
    user = User.login(
        request.form['username'],
        request.form['password'],
        session
    )
    if user is False:
        return redirect(
            url_for('login', message="Login failed, please try again.")
        )
    else:
        return redirect(url_for('index'))


@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))
# endregion


# region Index
@app.route("/")
def index():
    if User.login_required(session):
        return redirect(url_for('login'))

    configuration = Configuration.get()

    # region NASTY
    if configuration['month_start_date'] == "1":
        month_end_date = 28
    else:
        month_end_date = int(configuration['month_start_date']) - 1

    weekly_spending_calculations = calculations(
        int(configuration['weekly_spending_amount']),
        int(configuration['month_start_date']),
        month_end_date,
        int(configuration['weekly_pay_day'])
    )
    # endregion

    return render_template(
        'index.html',
        accounts=Account.query.order_by(Account.id).all(),
        outgoings=Outgoing.query.order_by(Outgoing.id).all(),
        total_outgoings=Outgoing.total(),
        salary=Salary.query.first(),
        configuration=configuration,
        weekly_spending_calculations=weekly_spending_calculations
    )
# endregion


# region Accounts
@app.route("/accounts")
def accounts():
    if User.login_required(session):
        return redirect(url_for('login'))

    return render_template(
        'accounts.html',
        accounts=Account.query.order_by(Account.id).all(),
    )


@app.route("/new-account")
def new_account():
    if User.login_required(session):
        return redirect(url_for('login'))

    return render_template('new-account.html')


@app.route("/new-account-handler")
def new_account_handler():
    if User.login_required(session):
        return redirect(url_for('login'))

    name = request.args.get("name")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    db.session.add(Account(name, notes=notes))
    db.session.commit()
    return redirect(url_for('accounts'))


@app.route("/edit-account/<account_id>")
def edit_account(account_id):
    if User.login_required(session):
        return redirect(url_for('login'))

    account = Account.query.get(account_id)
    return render_template('edit-account.html', account=account)


@app.route("/edit-account-handler/<account_id>")
def edit_account_handler(account_id):
    if User.login_required(session):
        return redirect(url_for('login'))

    name = request.args.get("name")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    account = Account.query.get(account_id)
    account.name = name
    account.notes = notes

    db.session.commit()
    return redirect(url_for('accounts'))


@app.route("/delete-account-handler/<account_id>")
def delete_account_handler(account_id):
    if User.login_required(session):
        return redirect(url_for('login'))

    account = Account.query.get(account_id)
    db.session.delete(account)

    db.session.commit()
    return redirect(url_for('accounts'))
# endregion


# region Outgoings
@app.route("/outgoings")
def outgoings():
    if User.login_required(session):
        return redirect(url_for('login'))

    return render_template(
        'outgoings.html',
        accounts=Account.query.order_by(Account.id).all()
    )


@app.route("/new-outgoing")
def new_outgoing():
    if User.login_required(session):
        return redirect(url_for('login'))

    account_id = request.args.get("account_id")
    return render_template(
        'new-outgoing.html',
        account_id=account_id,
        accounts=Account.query.order_by(Account.id).all()
    )


@app.route("/new-outgoing-handler")
def new_outgoing_handler():
    if User.login_required(session):
        return redirect(url_for('login'))

    account_id = request.args.get("account_id")
    name = request.args.get("name")
    value = request.args.get("value")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    db.session.add(Outgoing(name, value, account_id, notes=notes))
    db.session.commit()
    return redirect(url_for('outgoings'))


@app.route("/edit-outgoing/<outgoing_id>")
def edit_outgoing(outgoing_id):
    if User.login_required(session):
        return redirect(url_for('login'))

    outgoing = Outgoing.query.get(outgoing_id)
    return render_template(
        'edit-outgoing.html',
        accounts=Account.query.order_by(Account.id).all(),
        outgoing=outgoing
    )


@app.route("/edit-outgoing-handler/<outgoing_id>")
def edit_outgoing_handler(outgoing_id):
    if User.login_required(session):
        return redirect(url_for('login'))

    account_id = request.args.get("account_id")
    name = request.args.get("name")
    value = request.args.get("value")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    outgoing = Outgoing.query.get(outgoing_id)
    outgoing.account_id = account_id
    outgoing.name = name
    outgoing.value = value
    outgoing.notes = notes

    db.session.commit()
    return redirect(url_for('outgoings'))


@app.route("/delete-outgoing-handler/<outgoing_id>")
def delete_outgoing_handler(outgoing_id):
    if User.login_required(session):
        return redirect(url_for('login'))

    outgoing = Outgoing.query.get(outgoing_id)
    db.session.delete(outgoing)

    db.session.commit()
    return redirect(url_for('outgoings'))
# endregion


# region Configuration
@app.route("/configuration")
def configuration():
    if User.login_required(session):
        return redirect(url_for('login'))

    return render_template(
        'configuration.html',
        configuration=Configuration.get(),
        salary=Salary.query.first()
    )


@app.route("/configuration-handler")
def configuration_handler():
    if User.login_required(session):
        return redirect(url_for('login'))

    # Create a dict of the configuration objects
    configuration = {}
    for obj in Configuration.query.all():
        configuration[obj.name] = obj

    salary = Salary.query.first()

    # Update / Add All
    for arg, value in request.args.items():
        # Configuration Item
        if arg in CONFIGURATION_NAMES:
            try:
                configuration[arg].value = value
            except KeyError:
                db.session.add(Configuration(arg, value))
        # Salary Item
        else:
            try:
                setattr(salary, arg, value)
            except AttributeError:
                pass

    db.session.commit()
    return redirect(url_for(request.args.get('return_page', 'index')))
# endregion
