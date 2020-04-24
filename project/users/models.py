import datetime
from sqlalchemy import desc
from flask_login import UserMixin
from project import db, login_manager


@login_manager.user_loader
def load_user(user_obj):
    if user_obj["model"] == "admin":
        return Admin.query.get(user_obj["id"])
    elif user_obj["model"] == "user":
        return Users.query.get(user_obj["id"])


class Users(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    from_date = db.Column(db.DateTime, nullable=True)
    till_date = db.Column(db.DateTime, nullable=True)
    is_subscribed = db.Column(db.Boolean, default=False)
    subscription_plan = db.Column(db.String(100), nullable=True)
    insta_username = db.Column(db.String(100), unique=True, index=True)

    def is_authenticated(self):
        return True

    def get_id(self):
        return {"model": "user",
                "id": self.id}


class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'

    username = db.Column(db.String(256))
    password = db.Column(db.String(100))
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now())

    def get_id(self):
        return {"model": "admin",
                "id": self.id}


class Counter(db.Model):
    __tablename__ = "counter"

    id = db.Column(db.Integer, primary_key=True)
    insta_username = db.Column(db.String(100), index=True)
    input_request_count = db.Column(db.Integer, default=0)
    total_accepted_request = db.Column(db.Integer, default=0)
    total_failed_request = db.Column(db.Integer, default=0)
    is_request_complete = db.Column(db.Boolean, default=False)
    insert_date = db.Column(db.DateTime, default=datetime.datetime.now())
    update_date = db.Column(db.DateTime, default=datetime.datetime.now())

    def __init__(self, insta_username=None, **kwargs):
        self.insta_username = insta_username,
        self.input_request_count=kwargs.get("input_request_count", 0)
        self.total_accepted_request=kwargs.get("total_accepted_request", 0)
        self.total_failed_request=kwargs.get("total_failed_request", 0)
        self.insert_date=kwargs.get("insert_date", datetime.datetime.now())
        self.update_date=kwargs.get("update_date", datetime.datetime.now())

    def save(self):
        db.session.add(self)
        db.session.commit()

    def get_last_counter_info(self, user_name):
        last_counter_id = Counter.query.filter(Counter.insta_username==user_name).order_by(desc(Counter.id)).first()
        if last_counter_id is not None:
            self.id = last_counter_id.id
            return last_counter_id

    def update_follow_counter(self, success, failed):
        self.total_failed_request += failed
        self.total_accepted_request += success
        self.update_date = datetime.datetime.now()
        db.session.commit()

    def update_inc_failed_counter(self):
        self.update_date = datetime.datetime.now()
        self.total_failed_request += 1
        db.session.commit()

    def update_dec_failed_counter(self):
        self.update_date = datetime.datetime.now()
        self.total_failed_request -= 1
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


    @staticmethod
    def get_all_counter():
        return Counter.query.all()

    @staticmethod
    def get_one_counter(id):
        return Counter.query.get(id)

    def __repr__(self):
        return '<id {}>'.format(self.id)