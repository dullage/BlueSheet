import click
from main import db, User


@click.group()
def cli():
    pass


@click.command()
@click.option("--username", "-u")
@click.option("--password", "-p")
def add_user(username, password):
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


cli.add_command(add_user)
cli.add_command(unlock_user)


if __name__ == "__main__":
    cli()
