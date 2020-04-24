import click
import datetime

import sys
sys.path.append('../')
from project import db
from datetime import timedelta
from project.users.models import Users


@click.command()
@click.option('--username',  '-u', type=str, help='please enter a username')
def create_uesr(username):
    user = Users.query.filter_by(insta_username=username).first()
    if user:
        user.subscription_plan = 7
        user.from_date = datetime.datetime.now()
        user.till_date = datetime.datetime.now() + timedelta(days=int(7))
        user.is_subscribed = True
        db.session.commit()
        print("user table updated")
    else:
        print("user does not exist")


if __name__ == '__main__':
    create_uesr()