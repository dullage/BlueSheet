#!/usr/bin/python3

from datetime import date, datetime, timedelta
from functools import wraps
from os import environ

from dateutil.relativedelta import relativedelta
from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_sqlalchemy import SQLAlchemy

import helpers as h

SESSION_KEY = environ.get("SESSION_KEY")
if SESSION_KEY is None:
    print("Environment Variable SESSION_KEY not set!")
    exit(1)

PASSWORD_SALT = environ.get("PASSWORD_SALT")
if PASSWORD_SALT is None:
    print("Environment Variable PASSWORD_SALT not set!")
    exit(1)

LOGIN_TIMEOUT_MINUTES = 30
MAX_FAILED_LOGIN_ATTEMPTS = 3

app = Flask(__name__)
app.secret_key = SESSION_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get(
    "DATABASE_URL", "sqlite:///database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Define "permanent" as 1 year and not the default 31 days
app.permanent_session_lifetime = timedelta(days=365)


# region Database
class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    failed_login_attempts = db.Column(db.Integer, nullable=False)
    locked = db.Column(db.Boolean, nullable=False)
    configuration = db.relationship(
        "Configuration", backref="user", uselist=False, lazy=True
    )
    salary = db.relationship(
        "Salary", backref="user", uselist=False, lazy=True
    )
    accounts = db.relationship("Account", backref="user", lazy=True)
    outgoings = db.relationship("Outgoing", backref="user", lazy=True)
    annual_expenses = db.relationship(
        "AnnualExpense", backref="user", lazy=True
    )

    def __init__(self, username, password):
        self.username = username.lower()
        self.password = password
        self.failed_login_attempts = 0
        self.locked = False

    @classmethod
    def login(cls, username, password, remember, session):
        user = cls.query.filter_by(username=username.lower()).first()

        if user is None:
            return False, "Login failed, please try again."
        elif user.locked:
            return False, "Account locked, please contact your administrator."
        elif h.hash(password, PASSWORD_SALT) != user.password:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked = True
            db.session.commit()
            return False, "Login failed, please try again."
        else:
            user.failed_login_attempts = 0
            db.session.commit()

            # Stop the session from expiring when the browser closes
            session.permanent = True

            session["user_id"] = user.id
            session["last_activity"] = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            session["remember"] = h.checkbox_to_boolean(remember)

            return True, ""

    @classmethod
    def login_required(cls, func):
        """A decorator to go around routes that require login. If login is
        required a redirect to the login page is returned and the original
        function is not executed.
        """

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if "last_activity" not in session:
                return redirect(url_for("login"))
            if (
                datetime.strptime(
                    session["last_activity"], "%Y-%m-%d %H:%M:%S"
                )
                < (
                    datetime.now()
                    - relativedelta(minutes=LOGIN_TIMEOUT_MINUTES)
                )
                and session["remember"] is False
            ):
                return redirect(url_for("login"))
            else:
                session["last_activity"] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                return func(*args, **kwargs)

        return wrapped_func

    def configuration_required(self):
        """Checks to see if the user has completed configuration and returns
        True if not. This assumes that if configuration exists it is complete.
        """
        return self.configuration is None

    def total_outgoings(self, month_offset=0):
        """The total value of all of the users monthly outgoings."""
        total_outgoings = 0
        for outgoing in self.outgoings:
            if outgoing.is_current(month_offset=month_offset):
                total_outgoings += outgoing.value
        return total_outgoings

    @property
    def weekly_spending_calculations(self):
        tomorrow = date.today() + relativedelta(days=1)

        # If tommorow is the 1st, calculate as if it were tommorow as the
        # banking is done today, then add back in the weekly spending amount
        # that will be paid tomorrow.
        if tomorrow.day == 1:
            target = h.spending_money_savings_target_balance(
                self.configuration.weekly_pay_day,
                self.configuration.weekly_spending_amount,
                tomorrow,
            )
            if tomorrow.weekday() == self.configuration.weekly_pay_day:
                target = target + self.configuration.weekly_spending_amount
        # Else just calculate for today
        else:
            target = h.spending_money_savings_target_balance(
                self.configuration.weekly_pay_day,
                self.configuration.weekly_spending_amount,
            )

        return target


class Configuration(db.Model):
    __tablename__ = "configuration"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False
    )
    weekly_pay_day = db.Column(db.Integer, nullable=False)
    weekly_spending_amount = db.Column(db.Numeric, nullable=False)
    annual_expense_outgoing_id = db.Column(
        db.Integer, db.ForeignKey("outgoing.id")
    )

    def __init__(
        self,
        user_id,
        weekly_pay_day,
        weekly_spending_amount,
        annual_expense_outgoing_id=None,
    ):
        self.user_id = user_id
        self.weekly_pay_day = weekly_pay_day
        self.weekly_spending_amount = weekly_spending_amount
        self.annual_expense_outgoing_id = annual_expense_outgoing_id


class Salary(db.Model):
    __tablename__ = "salary"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False
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
        pension_contribution,
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
        return (self.annual_gross_salary - self.annual_tax_allowance) * (
            self.tax_rate / 100
        )

    @property
    def annual_ni(self):
        return (self.annual_gross_salary - self.annual_ni_allowance) * (
            self.ni_rate / 100
        )

    @property
    def annual_pension(self):
        return (
            self.annual_gross_salary - self.annual_non_pensionable_value
        ) * (self.pension_contribution / 100)

    @property
    def annual_pension_tax_relief(self):
        return self.annual_pension * (self.tax_rate / 100)

    @property
    def annual_net_salary(self):
        return (
            self.annual_gross_salary
            - self.annual_tax
            - self.annual_ni
            - self.annual_pension
            + self.annual_pension_tax_relief
        )


class Account(db.Model):
    __tablename__ = "account"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    notes = db.Column(db.String)
    outgoings = db.relationship("Outgoing", backref="account", lazy=True)

    def __init__(self, user_id, name, notes=None):
        self.user_id = user_id
        self.name = name
        self.notes = notes

    def total_outgoings(self, month_offset=0):
        """The total value of the accounts monthly outgoings."""
        total_outgoings = 0
        for outgoing in self.outgoings:
            if outgoing.is_current(month_offset=month_offset):
                total_outgoings = total_outgoings + outgoing.value
        return total_outgoings

    def delete(self):
        for outgoing in self.outgoings:
            outgoing.delete()
        db.session.delete(self)
        db.session.commit()


class Outgoing(db.Model):
    __tablename__ = "outgoing"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String, nullable=False)
    value = db.Column(db.Numeric, nullable=False)
    account_id = db.Column(
        db.Integer, db.ForeignKey("account.id"), nullable=False
    )
    start_month = db.Column(db.Date)
    end_month = db.Column(db.Date)
    notes = db.Column(db.String)

    def __init__(
        self,
        user_id,
        name,
        value,
        account_id,
        start_month=None,
        end_month=None,
        notes=None,
    ):
        self.user_id = user_id
        self.name = name
        self.value = value
        self.account_id = account_id
        self.start_month = start_month
        self.end_month = end_month
        self.notes = notes

    @property
    def start_month_input_string(self):
        return h.date_to_month_input(self.start_month)

    @property
    def end_month_input_string(self):
        return h.date_to_month_input(self.end_month)

    @property
    def start_month_friendly(self):
        if self.start_month is None:
            return ""
        else:
            return self.start_month.strftime("%B %Y")

    @property
    def end_month_friendly(self):
        if self.end_month is None:
            return ""
        else:
            return self.end_month.strftime("%B %Y")

    def is_future(self, month_offset=0):
        if self.start_month is None:
            return False

        comparison_date = date.today() + relativedelta(months=month_offset)

        if self.start_month > comparison_date:
            return True
        else:
            return False

    def is_historic(self, month_offset=0):
        if self.end_month is None:
            return False

        comparison_date = date.today() + relativedelta(months=month_offset)

        if self.end_month < comparison_date:
            return True
        else:
            return False

    def is_current(self, month_offset=0):
        if self.is_historic(month_offset=month_offset) or self.is_future(
            month_offset=month_offset
        ):
            return False
        else:
            return True

    @property
    def is_dated(self):
        if self.start_month is not None or self.end_month is not None:
            return True
        else:
            return False

    @property
    def months_paid(self):
        if self.start_month is None or self.end_month is None:
            return 0  # Not desinged to be used without start and end dates
        else:
            return h.month_count(self.start_month, self.end_month)

    @property
    def months_paid_left(self):
        if self.start_month is None or self.end_month is None:
            return 0  # Not desinged to be used without start and end dates
        else:
            return h.month_count(
                date.today() + relativedelta(months=1), self.end_month
            )

    @property
    def payments_total(self):
        if self.start_month is None or self.end_month is None:
            return 0  # Not desinged to be used without start and end dates
        else:
            return self.value * self.months_paid

    @property
    def payments_left_total(self):
        if self.start_month is None or self.end_month is None:
            return 0  # Not desinged to be used without start and end dates
        else:
            return self.value * self.months_paid_left

    @property
    def date_tooltip(self):
        if not self.is_dated:
            return ""

        today = date.today()

        # Start
        if self.start_month is None:
            start = ""
        elif self.start_month > today:
            start = "Starts"
        else:
            start = "Started"

        # End
        if self.end_month is None:
            end = ""
        elif self.end_month >= today:
            end = "Ends"
        else:
            end = "Ended"

        if self.start_month is not None and self.end_month is not None:
            # Start and End Months
            return "\n".join(
                [
                    f"{start} {self.start_month_friendly}",
                    f"{end} {self.end_month_friendly}",
                    "",
                    f"{self.months_paid} payment(s) overall totaling £{self.payments_total:,.2f}",
                    f"{self.months_paid_left} payment(s) left totaling £{self.payments_left_total:,.2f}",
                ]
            )
        elif self.start_month is not None:
            # Start Month Only
            return f"{start} {self.start_month_friendly}"
        else:
            # End Month Only
            return f"{end} {self.end_month_friendly}"

    def delete(self):
        # If this outgoing is used for annual expenses, unlink it first
        user_configuration = Configuration.query.filter_by(
            user_id=self.user_id
        ).first()
        if user_configuration.annual_expense_outgoing_id == self.id:
            user_configuration.annual_expense_outgoing_id = None

        db.session.delete(self)
        db.session.commit()


class AnnualExpense(db.Model):
    __tablename__ = "annual_expense"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    month_paid = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    value = db.Column(db.Numeric, nullable=False)
    notes = db.Column(db.String)

    def __init__(self, user_id, month_paid, name, value, notes=None):
        self.user_id = user_id
        self.month_paid = month_paid
        self.name = name
        self.value = value
        self.notes = notes

    @classmethod
    def by_month_range(cls, user, start_month_num, end_month_num):
        """Returns a list of AnnualExpense objects given a User id and a
        target month."""
        return cls.query.filter(
            cls.user_id == user.id,
            cls.month_paid >= start_month_num,
            cls.month_paid <= end_month_num,
        )

    @classmethod
    def annual_total(cls, user):
        annual_expenses = cls.query.filter_by(user_id=user.id)

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
        current_month = h.current_month_num()

        # Start the simulation next month as the presumption is that this
        # month has already been saved and spent.
        working_month = h.next_month(current_month)
        ending_month = current_month

        working_balance = 0
        lowest_balance = 999999999  # Initialise

        # Simulate a year.
        while True:
            # Add saving at the begining of the month.
            working_balance = working_balance + monthly_saving

            # Pay out the expenses throughout the month.
            for annual_expense in cls.query.filter_by(
                user_id=user.id, month_paid=working_month
            ):
                working_balance = working_balance - annual_expense.value

            # If this is the lowest balance we've seen, record it.
            if working_balance < lowest_balance:
                lowest_balance = working_balance

            if working_month == ending_month:
                break
            else:
                working_month = h.next_month(working_month)

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
                    outgoing.start_month = None
                    outgoing.end_month = None
            db.session.commit()
            return

    def delete(self):
        db.session.delete(self)
        db.session.commit()


db.create_all()
db.session.commit()


def env_user():
    username = environ.get("USERNAME")
    if username is None:
        return

    password = environ.get("PASSWORD")
    if password is None:
        return

    existing_user = User.query.filter_by(username=username.lower()).first()
    if existing_user is None:
        db.session.add(User(username, password))
    else:
        existing_user.password = h.hash(password, PASSWORD_SALT)

    db.session.commit()


env_user()
# endregion


# region Routes
# region Login
@app.route("/login")
def login():
    message = request.args.get("message")
    return render_template("login.html", message=message)


@app.route("/login-handler", methods=["POST"])
def login_handler():
    login_result = User.login(
        request.form["username"],
        request.form["password"],
        request.form.get("remember"),
        session,
    )
    if login_result[0] is not True:
        return redirect(url_for("login", message=login_result[1]))
    else:
        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# endregion


# region Index
@app.route("/")
@User.login_required
def index():
    user = User.query.get(session["user_id"])

    if user.configuration_required():
        return redirect(url_for("configuration"))

    current_month = h.current_month_num()
    current_month_annual_expenses = AnnualExpense.by_month_range(
        user, current_month, current_month
    )
    end_of_month_target_balance = AnnualExpense.end_of_month_target_balance(
        user
    )

    return render_template(
        "index.html",
        user=user,
        current_month_annual_expenses=current_month_annual_expenses,
        end_of_month_target_balance=end_of_month_target_balance,
    )


# endregion

# region Configuration
@app.route("/configuration")
@User.login_required
def configuration():
    user = User.query.get(session["user_id"])

    return render_template("configuration.html", user=user)


@app.route("/configuration-handler", methods=["POST"])
@User.login_required
def configuration_handler():
    user = User.query.get(session["user_id"])

    form_data = h.empty_strings_to_none(request.form)

    form_data["month_start_date"] = 28  # Hardcode for now.

    if user.configuration is None:
        db.session.add(
            Configuration(
                user.id,
                form_data["weekly_pay_day"],
                form_data["weekly_spending_amount"],
                form_data["annual_expense_outgoing_id"],
            )
        )
    else:
        user.configuration.weekly_pay_day = form_data["weekly_pay_day"]
        user.configuration.weekly_spending_amount = form_data[
            "weekly_spending_amount"
        ]
        user.configuration.annual_expense_outgoing_id = form_data[
            "annual_expense_outgoing_id"
        ]

    if user.salary is None:
        db.session.add(
            Salary(
                user.id,
                form_data["annual_gross_salary"],
                form_data["annual_tax_allowance"],
                form_data["tax_rate"],
                form_data["annual_ni_allowance"],
                form_data["ni_rate"],
                form_data["annual_non_pensionable_value"],
                form_data["pension_contribution"],
            )
        )
    else:
        user.salary.annual_gross_salary = form_data["annual_gross_salary"]
        user.salary.annual_tax_allowance = form_data["annual_tax_allowance"]
        user.salary.tax_rate = form_data["tax_rate"]
        user.salary.annual_ni_allowance = form_data["annual_ni_allowance"]
        user.salary.ni_rate = form_data["ni_rate"]
        user.salary.annual_non_pensionable_value = form_data[
            "annual_non_pensionable_value"
        ]
        user.salary.pension_contribution = form_data["pension_contribution"]

    db.session.commit()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for(form_data.get("return_page", "index")))


# endregion


# region Accounts
@app.route("/accounts")
@User.login_required
def accounts():
    user = User.query.get(session["user_id"])

    return render_template("accounts.html", user=user)


@app.route("/new-account")
@User.login_required
def new_account():
    return render_template("new-account.html")


@app.route("/new-account-handler", methods=["POST"])
@User.login_required
def new_account_handler():
    user = User.query.get(session["user_id"])

    form_data = h.empty_strings_to_none(request.form)

    db.session.add(Account(user.id, form_data["name"], form_data["notes"]))
    db.session.commit()

    return redirect(url_for("accounts"))


@app.route("/edit-account/<account_id>")
@User.login_required
def edit_account(account_id):
    user = User.query.get(session["user_id"])

    return render_template(
        "edit-account.html",
        account=Account.query.filter_by(
            user_id=user.id, id=account_id
        ).first(),
    )


@app.route("/edit-account-handler/<account_id>", methods=["POST"])
@User.login_required
def edit_account_handler(account_id):
    user = User.query.get(session["user_id"])

    form_data = h.empty_strings_to_none(request.form)

    account = Account.query.filter_by(user_id=user.id, id=account_id).first()

    account.name = form_data["name"]
    account.notes = form_data["notes"]

    db.session.commit()

    return redirect(url_for("accounts"))


@app.route("/delete-account-handler/<account_id>")
@User.login_required
def delete_account_handler(account_id):
    user = User.query.get(session["user_id"])

    account = Account.query.filter_by(user_id=user.id, id=account_id).first()

    account.delete()

    return redirect(url_for("accounts"))


# endregion


# region Montly Outgoings
@app.route("/outgoings")
@User.login_required
def outgoings():
    user = User.query.get(session["user_id"])

    return render_template(
        "outgoings.html", user=user, todays_date=date.today()
    )


@app.route("/new-outgoing")
@User.login_required
def new_outgoing():
    user = User.query.get(session["user_id"])

    # Note: This does no harm if the id is another users. It's only used to
    # auto select a selection input.
    account_id = request.args.get("account_id")

    return render_template(
        "new-outgoing.html", user=user, account_id=account_id
    )


@app.route("/new-outgoing-handler", methods=["POST"])
@User.login_required
def new_outgoing_handler():
    user = User.query.get(session["user_id"])

    form_data = h.empty_strings_to_none(request.form)

    db.session.add(
        Outgoing(
            user.id,
            form_data["name"],
            form_data["value"],
            form_data["account_id"],
            start_month=h.month_input_to_date(form_data["start_month"]),
            end_month=h.month_input_to_date(
                form_data["end_month"], set_to_last_day=True
            ),
            notes=form_data["notes"],
        )
    )
    db.session.commit()

    return redirect(url_for("outgoings"))


@app.route("/edit-outgoing/<outgoing_id>")
@User.login_required
def edit_outgoing(outgoing_id):
    user = User.query.get(session["user_id"])

    return render_template(
        "edit-outgoing.html",
        user=user,
        outgoing=Outgoing.query.filter_by(
            user_id=user.id, id=outgoing_id
        ).first(),
    )


@app.route("/edit-outgoing-handler/<outgoing_id>", methods=["POST"])
@User.login_required
def edit_outgoing_handler(outgoing_id):
    user = User.query.get(session["user_id"])

    form_data = h.empty_strings_to_none(request.form)

    outgoing = Outgoing.query.filter_by(
        user_id=user.id, id=outgoing_id
    ).first()

    outgoing.account_id = form_data["account_id"]
    outgoing.name = form_data["name"]
    outgoing.value = form_data["value"]
    outgoing.start_month = h.month_input_to_date(form_data.get("start_month"))
    outgoing.end_month = h.month_input_to_date(
        form_data.get("end_month"), set_to_last_day=True
    )
    outgoing.notes = form_data["notes"]

    db.session.commit()

    return redirect(url_for("outgoings"))


@app.route("/delete-outgoing-handler/<outgoing_id>")
@User.login_required
def delete_outgoing_handler(outgoing_id):
    user = User.query.get(session["user_id"])

    outgoing = Outgoing.query.filter_by(
        user_id=user.id, id=outgoing_id
    ).first()

    outgoing.delete()

    return redirect(url_for("outgoings"))


# endregion


# region Annual Expenses
@app.route("/annual-expenses")
@User.login_required
def annual_expenses():
    user = User.query.get(session["user_id"])

    return render_template("annual-expenses.html", user=user, months=h.months)


@app.route("/new-annual-expense")
@User.login_required
def new_annual_expense():
    user = User.query.get(session["user_id"])

    return render_template(
        "new-annual-expense.html", user=user, months=h.months
    )


@app.route("/new-annual-expense-handler", methods=["POST"])
@User.login_required
def new_annual_expense_handler():
    user = User.query.get(session["user_id"])

    form_data = h.empty_strings_to_none(request.form)

    db.session.add(
        AnnualExpense(
            user.id,
            form_data["month_paid"],
            form_data["name"],
            form_data["value"],
            form_data["notes"],
        )
    )
    db.session.commit()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for("annual_expenses"))


@app.route("/edit-annual-expense/<annual_expense_id>")
@User.login_required
def edit_annual_expense(annual_expense_id):
    user = User.query.get(session["user_id"])

    return render_template(
        "edit-annual-expense.html",
        user=user,
        annual_expense=AnnualExpense.query.filter_by(
            user_id=user.id, id=annual_expense_id
        ).first(),
        months=h.months,
    )


@app.route(
    "/edit-annual-expense-handler/<annual_expense_id>", methods=["POST"]
)
@User.login_required
def edit_annual_expense_handler(annual_expense_id):
    user = User.query.get(session["user_id"])

    form_data = h.empty_strings_to_none(request.form)

    annual_expense = AnnualExpense.query.filter_by(
        user_id=user.id, id=annual_expense_id
    ).first()

    annual_expense.month_paid = form_data["month_paid"]
    annual_expense.name = form_data["name"]
    annual_expense.value = form_data["value"]
    annual_expense.notes = form_data["notes"]

    db.session.commit()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for("annual_expenses"))


@app.route("/delete-annual-expense-handler/<annual_expense_id>")
@User.login_required
def delete_annual_expense_handler(annual_expense_id):
    user = User.query.get(session["user_id"])

    annual_expense = AnnualExpense.query.filter_by(
        user_id=user.id, id=annual_expense_id
    ).first()

    annual_expense.delete()

    AnnualExpense.update_user_annual_expense_outgoing(user)

    return redirect(url_for("annual_expenses"))


# endregion
# endregion
