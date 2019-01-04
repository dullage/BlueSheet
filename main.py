#!/usr/bin/python3
from flask import Flask, render_template, request, redirect, url_for, \
    session, jsonify
from flask_sqlalchemy import SQLAlchemy
from helpers import empty_strings_to_none, demo_starling_account, \
    months, next_month, current_month_num, \
    spending_money_savings_target_balance
from datetime import datetime, timedelta
from os import environ, urandom
from starlingbank import StarlingAccount

LOGIN_TIMEOUT_MINUTES = 30
MAX_FAILED_LOGIN_ATTEMPTS = 3

app = Flask(__name__)

# If the environment variable SECRET_KEY is not set a new secret key will be
# generated each time the app starts. Note: This invaldates any existing
# sessions.
app.secret_key \
    = environ.get('SECRET_KEY', urandom(16))

app.config['SQLALCHEMY_DATABASE_URI'] \
    = f"sqlite:///{environ.get('DATABASE_PATH', 'BlueSheet.db')}"

db = SQLAlchemy(app)


# region Database
class User(db.Model):
    __tablename__ = "user"
    _failed_login_attempts = 0

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    failed_login_attempts = db.Column(db.Integer, nullable=False)
    locked = db.Column(db.Boolean, nullable=False)
    configuration = db.relationship(
        "Configuration",
        backref="user",
        uselist=False,
        lazy=True
    )
    salary = db.relationship(
        "Salary",
        backref="user",
        uselist=False,
        lazy=True
    )
    accounts = db.relationship(
        "Account",
        backref="user",
        lazy=True
    )
    outgoings = db.relationship(
        "Outgoing",
        backref="user",
        lazy=True
    )
    annual_expenses = db.relationship(
        "AnnualExpense",
        backref="user",
        lazy=True
    )

    def __init__(self, username, password):
        self.id - id
        self.username = username
        self.password = password
        self.failed_login_attempts = 0
        self.locked = False

    @classmethod
    def login(cls, username, password, session):
        user = User.query.filter_by(username=username).first()

        if user is None:
            return False, "Login failed, please try again."
        elif user.locked:
            return False, "Account locked, please contact your administrator."
        elif user.password != password:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked = True
            db.session.commit()
            return False, "Login failed, please try again."
        else:
            user.failed_login_attempts = 0
            db.session.commit()

            session['user_id'] = user.id
            session['last_activity'] = \
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            return True, ""

    @classmethod
    def login_required(cls, session):
        """Carries out a number of checks and returns True if the user needs
        to log in again.
        """
        if 'user_id' not in session:
            return True
        if 'last_activity' not in session:
            return True
        if datetime.strptime(session['last_activity'], '%Y-%m-%d %H:%M:%S') \
                < (datetime.now() - timedelta(minutes=LOGIN_TIMEOUT_MINUTES)):
            return True
        else:
            session['last_activity'] = \
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return False

    def configuration_required(self):
        """Checks to see if the user has completed configuration and returns
        True if not. This assumes that if configuration exists it is complete.
        """
        if self.configuration is None:
            return True
        else:
            return False

    @property
    def total_outgoings(self):
        """The total value of all of the users monthly outgoings."""
        total_outgoings = 0
        for outgoing in self.outgoings:
            total_outgoings = total_outgoings + outgoing.value
        return total_outgoings

    @property
    def weekly_spending_calculations(self):
        return spending_money_savings_target_balance(
            self.configuration.weekly_pay_day,
            self.configuration.weekly_spending_amount
        )

    @property
    def starling_account(self):
        if self.configuration.starling_api_key is None:
            return None
        elif self.username == "demo":
            return demo_starling_account
        else:
            try:
                return StarlingAccount(
                    self.configuration.starling_api_key,
                    update=True
                )
            except: # noqa
                return None


class Configuration(db.Model):
    __tablename__ = "configuration"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        unique=True,
        nullable=False
    )
    weekly_pay_day = db.Column(db.Integer, nullable=False)
    weekly_spending_amount = db.Column(db.Numeric, nullable=False)
    annual_expense_outgoing_id = db.Column(
        db.Integer,
        db.ForeignKey('outgoing.id')
    )
    starling_api_key = db.Column(db.String(255))

    def __init__(
        self,
        user_id,
        weekly_pay_day,
        weekly_spending_amount,
        annual_expense_outgoing_id=None,
        starling_api_key=None
    ):
        self.user_id = user_id
        self.weekly_pay_day = weekly_pay_day
        self.weekly_spending_amount = weekly_spending_amount
        self.annual_expense_outgoing_id = annual_expense_outgoing_id
        self.starling_api_key = starling_api_key


class Salary(db.Model):
    __tablename__ = "salary"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        unique=True,
        nullable=False
    )
    annual_gross_salary = db.Column(db.Numeric, nullable=False)
    annual_tax_allowance = db.Column(db.Numeric, nullable=False)
    tax_rate = db.Column(db.Numeric, nullable=False)
    annual_ni_allowance = db.Column(db.Numeric, nullable=False)
    ni_rate = db.Column(db.Numeric, nullable=False)
    annual_non_pensionable_value = db.Column(db.Numeric, nullable=False)
    pension_contribution = db.Column(db.Numeric, nullable=False)

    def __init__(
        self,
        user_id,
        annual_gross_salary,
        annual_tax_allowance,
        tax_rate,
        annual_ni_allowance,
        ni_rate,
        annual_non_pensionable_value,
        pension_contribution
    ):
        self.user_id = user_id
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.String(8000))
    outgoings = db.relationship("Outgoing", backref="account", lazy=True)

    def __init__(self, user_id, name, notes=None):
        self.user_id = user_id
        self.name = name
        self.notes = notes


class Outgoing(db.Model):
    __tablename__ = "outgoing"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Numeric, nullable=False)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey('account.id'),
        nullable=False
    )
    notes = db.Column(db.String(8000))

    def __init__(self, user_id, name, value, account_id, notes=None):
        self.user_id = user_id
        self.name = name
        self.value = value
        self.account_id = account_id
        self.notes = notes


class AnnualExpense(db.Model):
    __tablename__ = "annual_expense"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    month_paid = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Numeric, nullable=False)
    notes = db.Column(db.String(8000))

    def __init__(self, user_id, month_paid, name, value, notes=None):
        self.user_id = user_id
        self.month_paid = month_paid
        self.name = name
        self.value = value
        self.notes = notes

    @classmethod
    def by_month_range(cls, user, start_month_num, end_month_num):
        """Returns a list of AnnualExpense objects
        given a User id and a target month."""
        return cls.query.filter(
            cls.user_id == user.id,
            cls.month_paid >= start_month_num,
            cls.month_paid <= end_month_num
        )

    @classmethod
    def annual_total(cls, user):
        annual_expenses = cls.query.filter_by(
            user_id=user.id
        )

        annual_total = 0
        for annual_expense in annual_expenses:
            annual_total = annual_total + annual_expense.value

        return annual_total

    @classmethod
    def monthly_saving(cls, user):
        return cls.annual_total(user) / 12

    @classmethod
    def end_of_month_target_balance(cls, user):
        """Runs a year long simulation of annual expense savings and expenses
        and if at any point the account balance goes into the negative that
        negative amount is returned as a positive current target balance.
        """
        monthly_saving = cls.monthly_saving(user)
        current_month = current_month_num()

        # Start the simulation next month as the presumption is that this
        # month has already been saved and spent.
        working_month = next_month(current_month)
        ending_month = current_month

        working_balance = 0
        lowest_balance = 999999999  # Initialise

        # Simulate a year.
        while True:
            # Add saving at the begining of the month.
            working_balance = working_balance + monthly_saving

            # Pay out the expenses throughout the month.
            for annual_expense in cls.query.filter_by(
                user_id=user.id,
                month_paid=working_month
            ):
                working_balance = working_balance - annual_expense.value

            # If this is the lowest balance we've seen, record it.
            if working_balance < lowest_balance:
                lowest_balance = working_balance

            if working_month == ending_month:
                break
            else:
                working_month = next_month(working_month)

        return -lowest_balance

    @classmethod
    def update_user_annual_expense_outgoing(cls, user):
        outgoing_id = user.configuration.annual_expense_outgoing_id

        if outgoing_id is None:
            return
        else:
            for outgoing in user.outgoings:
                if outgoing.id == outgoing_id:
                    outgoing.value = cls.monthly_saving(user)
            db.session.commit()
            return


db.create_all()
# endregion


# region Routes
# region Login
@app.route("/login")
def login():
    message = request.args.get('message')
    return render_template(
        'login.html',
        message=message
    )


@app.route("/login-handler", methods=['POST'])
def login_handler():
    login_result = User.login(
        request.form['username'],
        request.form['password'],
        session
    )
    if login_result[0] is not True:
        return redirect(
            url_for('login', message=login_result[1])
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
    user = User.query.get(session['user_id'])

    if user.configuration_required():
        return redirect(url_for('configuration'))

    current_month = current_month_num()
    current_month_annual_expenses = AnnualExpense.by_month_range(
        user,
        current_month,
        current_month
    )
    end_of_month_target_balance = \
        AnnualExpense.end_of_month_target_balance(user)

    return render_template(
        'index.html',
        user=user,
        current_month_annual_expenses=current_month_annual_expenses,
        end_of_month_target_balance=end_of_month_target_balance
    )
# endregion


# region Starling Integration
@app.route("/get-starling-data")
def get_starling_data():
    if User.login_required(session):
        return "Session Expired!", 401
    user = User.query.get(session['user_id'])

    data = {
        "Main Balance": "£ {:.2f}".format(
            user.starling_account.effective_balance
        )
    }
    for uid, savings_goal in user.starling_account.savings_goals.items():
        data[savings_goal.name] \
            = "£ {:.2f}".format(savings_goal.total_saved_minor_units / 100)

    return jsonify(data)
# endregion


# region Configuration
@app.route("/configuration")
def configuration():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'configuration.html',
        user=user
    )


@app.route("/configuration-handler", methods=['POST'])
def configuration_handler():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    form_data = empty_strings_to_none(request.form)

    form_data['month_start_date'] = 28  # Hardcode for now.

    if user.configuration is None:
        db.session.add(Configuration(
            user.id,
            form_data['weekly_pay_day'],
            form_data['weekly_spending_amount'],
            form_data['annual_expense_outgoing_id'],
            form_data['starling_api_key']
        ))
    else:
        user.configuration.weekly_pay_day = form_data['weekly_pay_day']
        user.configuration.weekly_spending_amount \
            = form_data['weekly_spending_amount']
        user.configuration.annual_expense_outgoing_id \
            = form_data['annual_expense_outgoing_id']
        user.configuration.starling_api_key = form_data['starling_api_key']

    if user.salary is None:
        db.session.add(Salary(
            user.id,
            form_data['annual_gross_salary'],
            form_data['annual_tax_allowance'],
            form_data['tax_rate'],
            form_data['annual_ni_allowance'],
            form_data['ni_rate'],
            form_data['annual_non_pensionable_value'],
            form_data['pension_contribution']
        ))
    else:
        user.salary.annual_gross_salary = form_data['annual_gross_salary']
        user.salary.annual_tax_allowance = form_data['annual_tax_allowance']
        user.salary.tax_rate = form_data['tax_rate']
        user.salary.annual_ni_allowance = form_data['annual_ni_allowance']
        user.salary.ni_rate = form_data['ni_rate']
        user.salary.annual_non_pensionable_value \
            = form_data['annual_non_pensionable_value']
        user.salary.pension_contribution = form_data['pension_contribution']

    db.session.commit()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for(form_data.get('return_page', 'index')))
# endregion


# region Accounts
@app.route("/accounts")
def accounts():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'accounts.html',
        user=user
    )


@app.route("/new-account")
def new_account():
    if User.login_required(session):
        return redirect(url_for('login'))

    return render_template('new-account.html')


@app.route("/new-account-handler", methods=['POST'])
def new_account_handler():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    form_data = empty_strings_to_none(request.form)

    db.session.add(Account(
        user.id,
        form_data['name'],
        form_data['notes']
    ))
    db.session.commit()

    return redirect(url_for('accounts'))


@app.route("/edit-account/<account_id>")
def edit_account(account_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'edit-account.html',
        account=Account.query.filter_by(
            user_id=user.id,
            id=account_id,
        ).first()
    )


@app.route("/edit-account-handler/<account_id>", methods=['POST'])
def edit_account_handler(account_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    form_data = empty_strings_to_none(request.form)

    account = Account.query.filter_by(
        user_id=user.id,
        id=account_id,
    ).first()

    account.name = form_data['name']
    account.notes = form_data['notes']

    db.session.commit()

    return redirect(url_for('accounts'))


@app.route("/delete-account-handler/<account_id>")
def delete_account_handler(account_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    account = Account.query.filter_by(
        user_id=user.id,
        id=account_id,
    ).first()

    db.session.delete(account)

    db.session.commit()

    return redirect(url_for('accounts'))
# endregion


# region Montly Outgoings
@app.route("/outgoings")
def outgoings():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'outgoings.html',
        user=user
    )


@app.route("/new-outgoing")
def new_outgoing():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    # Note: This does no harm if the id is another users. It's only used to
    # auto select a selection input.
    account_id = request.args.get("account_id")

    return render_template(
        'new-outgoing.html',
        user=user,
        account_id=account_id
    )


@app.route("/new-outgoing-handler", methods=['POST'])
def new_outgoing_handler():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    form_data = empty_strings_to_none(request.form)

    db.session.add(Outgoing(
        user.id,
        form_data['name'],
        form_data['value'],
        form_data['account_id'],
        form_data['notes']
    ))
    db.session.commit()

    return redirect(url_for('outgoings'))


@app.route("/edit-outgoing/<outgoing_id>")
def edit_outgoing(outgoing_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'edit-outgoing.html',
        user=user,
        outgoing=Outgoing.query.filter_by(
            user_id=user.id,
            id=outgoing_id
        ).first()
    )


@app.route("/edit-outgoing-handler/<outgoing_id>", methods=['POST'])
def edit_outgoing_handler(outgoing_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    form_data = empty_strings_to_none(request.form)

    outgoing = Outgoing.query.filter_by(
        user_id=user.id,
        id=outgoing_id
    ).first()

    outgoing.account_id = form_data['account_id']
    outgoing.name = form_data['name']
    outgoing.value = form_data['value']
    outgoing.notes = form_data['notes']

    db.session.commit()

    return redirect(url_for('outgoings'))


@app.route("/delete-outgoing-handler/<outgoing_id>")
def delete_outgoing_handler(outgoing_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    outgoing = Outgoing.query.filter_by(
        user_id=user.id,
        id=outgoing_id
    ).first()

    db.session.delete(outgoing)

    db.session.commit()

    return redirect(url_for('outgoings'))
# endregion


# region Annual Expenses
@app.route("/annual-expenses")
def annual_expenses():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'annual-expenses.html',
        user=user,
        months=months
    )


@app.route("/new-annual-expense")
def new_annual_expense():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'new-annual-expense.html',
        user=user,
        months=months
    )


@app.route("/new-annual-expense-handler", methods=['POST'])
def new_annual_expense_handler():
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    form_data = empty_strings_to_none(request.form)

    db.session.add(AnnualExpense(
        user.id,
        form_data['month_paid'],
        form_data['name'],
        form_data['value'],
        form_data['notes']
    ))
    db.session.commit()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for('annual_expenses'))


@app.route("/edit-annual-expense/<annual_expense_id>")
def edit_annual_expense(annual_expense_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    return render_template(
        'edit-annual-expense.html',
        user=user,
        annual_expense=AnnualExpense.query.filter_by(
            user_id=user.id,
            id=annual_expense_id
        ).first(),
        months=months
    )


@app.route("/edit-annual-expense-handler/<annual_expense_id>",
           methods=['POST']
           )
def edit_annual_expense_handler(annual_expense_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    form_data = empty_strings_to_none(request.form)

    annual_expense = AnnualExpense.query.filter_by(
        user_id=user.id,
        id=annual_expense_id
    ).first()

    annual_expense.month_paid = form_data['month_paid']
    annual_expense.name = form_data['name']
    annual_expense.value = form_data['value']
    annual_expense.notes = form_data['notes']

    db.session.commit()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for('annual_expenses'))


@app.route("/delete-annual-expense-handler/<annual_expense_id>")
def delete_annual_expense_handler(annual_expense_id):
    if User.login_required(session):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    annual_expense = AnnualExpense.query.filter_by(
        user_id=user.id,
        id=annual_expense_id
    ).first()

    db.session.delete(annual_expense)

    db.session.commit()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for('annual_expenses'))
# endregion
# endregion
