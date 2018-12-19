from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import math

DATABASE_NAME = 'BlueSheet.db'
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_NAME}'

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(math.floor(n/10)%10!=1)*(n%10<4)*n%10::4])  # noqa


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


class Accounts(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.String(8000))
    outgoings = db.relationship("Outgoings", backref="account", lazy=True)

    def __init__(self, name, notes=None):
        self.name = name
        self.notes = notes


class Outgoings(db.Model):
    __tablename__ = "outgoings"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Numeric, nullable=False)
    account_id = db.Column(
        db.Integer,
        db.ForeignKey('accounts.id'),
        nullable=False
    )
    notes = db.Column(db.String(8000))

    def __init__(self, name, value, account_id, notes=None):
        self.name = name
        self.value = value
        self.account_id = account_id
        self.notes = notes


db.create_all()

# Default Configuration
# try:
#     db.session.add(Configuration('month_start_date', '1'))
# except:
#     pass

# db.session.commit()


# Index
@app.route("/")
def index():
    return render_template(
        'index.html',
        accounts=Accounts.query.order_by(Accounts.id).all(),
        outgoings=Outgoings.query.order_by(Outgoings.id).all(),
        configuration=Configuration.get()
    )


# Accounts
@app.route("/accounts")
def accounts():
    return render_template(
        'accounts.html',
        accounts=Accounts.query.order_by(Accounts.id).all(),
    )


@app.route("/new-account")
def new_account():
    return render_template('new-account.html')


@app.route("/new-account-handler")
def new_account_handler():
    name = request.args.get("name")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    db.session.add(Accounts(name, notes=notes))
    db.session.commit()
    return redirect(url_for('accounts'))


@app.route("/edit-account/<account_id>")
def edit_account(account_id):
    account = Accounts.query.get(account_id)
    return render_template('edit-account.html', account=account)


@app.route("/edit-account-handler/<account_id>")
def edit_account_handler(account_id):
    name = request.args.get("name")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    account = Accounts.query.get(account_id)
    account.name = name
    account.notes = notes

    db.session.commit()
    return redirect(url_for('accounts'))


@app.route("/delete-account-handler/<account_id>")
def delete_account_handler(account_id):
    account = Accounts.query.get(account_id)
    db.session.delete(account)

    db.session.commit()
    return redirect(url_for('accounts'))


# Outgoings
@app.route("/outgoings")
def outgoings():
    return render_template(
        'outgoings.html',
        accounts=Accounts.query.order_by(Accounts.id).all()
    )


@app.route("/new-outgoing")
def new_outgoing():
    account_id = request.args.get("account_id")
    return render_template(
        'new-outgoing.html',
        account_id=account_id,
        accounts=Accounts.query.order_by(Accounts.id).all()
    )


@app.route("/new-outgoing-handler")
def new_outgoing_handler():
    account_id = request.args.get("account_id")
    name = request.args.get("name")
    value = request.args.get("value")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    db.session.add(Outgoings(name, value, account_id, notes=notes))
    db.session.commit()
    return redirect(url_for('outgoings'))


@app.route("/edit-outgoing/<outgoing_id>")
def edit_outgoing(outgoing_id):
    outgoing = Outgoings.query.get(outgoing_id)
    return render_template(
        'edit-outgoing.html',
        accounts=Accounts.query.order_by(Accounts.id).all(),
        outgoing=outgoing
    )


@app.route("/edit-outgoing-handler/<outgoing_id>")
def edit_outgoing_handler(outgoing_id):
    account_id = request.args.get("account_id")
    name = request.args.get("name")
    value = request.args.get("value")
    notes = request.args.get("notes")
    if notes == "":
        notes = None

    outgoing = Outgoings.query.get(outgoing_id)
    outgoing.account_id = account_id
    outgoing.name = name
    outgoing.value = value
    outgoing.notes = notes

    db.session.commit()
    return redirect(url_for('outgoings'))


@app.route("/delete-outgoing-handler/<outgoing_id>")
def delete_outgoing_handler(outgoing_id):
    outgoing = Outgoings.query.get(outgoing_id)
    db.session.delete(outgoing)

    db.session.commit()
    return redirect(url_for('outgoings'))


# Configuration
@app.route("/configuration")
def configuration():
    return render_template(
        'configuration.html',
        configuration=Configuration.get()
    )


@app.route("/configuration-handler")
def configuration_handler():
    # Create a dict of the configuration objects
    configuration = {}
    configuration_objs = Configuration.query.all()
    for obj in configuration_objs:
        configuration[obj.name] = obj

    # Update / Add All
    for arg, value in request.args.items():
        if arg in configuration:
            configuration[arg].value = value
        else:
            db.session.add(Configuration(arg, value))

    db.session.commit()
    return redirect(url_for('index'))
