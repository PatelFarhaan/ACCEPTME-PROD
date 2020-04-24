import click

import sys
sys.path.append('../')
from project import db
from project.users.models import Admin
from werkzeug.security import generate_password_hash


@click.command()
@click.option('--username', '-u', type=str, help='Enter the username of the admin')
@click.option('--password', '-p', type=str, help='Enter the password of the admin')
def admin_password(username, password):
    Admin.query.delete()
    hashed_password = generate_password_hash(password)
    # noinspection PyArgumentList
    new_admin = Admin(username=username, password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()
    print("new user created")


if __name__ == '__main__':
    admin_password()