import datetime
from project import db
from project.users.models import Users


def check_subscription(user_name):
    user = Users.query.filter_by(insta_username=user_name).first()
    if user is not None:
        if user.is_subscribed:
            if datetime.datetime.now() > user.till_date:
                user.till_date=None
                user.from_date=None
                user.is_subscribed=False
                db.session.commit()
                return False
            else:
                return True
        else:
            return False
    else:
        new_user = Users(insta_username=user_name)
        db.session.add(new_user)
        db.session.commit()
        return False