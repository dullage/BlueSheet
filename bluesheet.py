import click

from helpers import hash
from main import PASSWORD_SALT, User, db


@click.group()
def cli():
    pass


@click.command()
@click.option("--username", "-u")
@click.option("--password", "-p")
def add_user(username, password):
    password = hash(password, PASSWORD_SALT)

    db.session.add(User(
        username=username,
        password=password
    ))

    db.session.commit()


@click.command()
@click.option("--username", "-u")
def unlock_user(username):
    user = User.query.filter_by(
        username=username
    ).first()

    user.locked = False
    user.failed_login_attempts = 0

    db.session.commit()


@click.command()
@click.option("--username", "-u")
@click.option("--password", "-p")
def change_password(username, password):
    user = User.query.filter_by(
        username=username
    ).first()

    user.password = hash(password, PASSWORD_SALT)
    print(user.password)

    db.session.commit()


cli.add_command(add_user)
cli.add_command(unlock_user)
cli.add_command(change_password)


if __name__ == "__main__":
    cli()
