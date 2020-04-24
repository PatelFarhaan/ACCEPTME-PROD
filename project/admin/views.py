import sys
sys.path.append('../../')

import datetime
from project import db
from datetime import timedelta
from project.users.models import Admin
from project.users.models import Users
from werkzeug.security import check_password_hash
from flask_login import login_required, login_user, logout_user
from flask import Blueprint, redirect, request, render_template, url_for


admins_blueprint = Blueprint('admin', __name__, template_folder='templates')


@admins_blueprint.route('/acceptme-portal', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['admin_email']
        admin_password = request.form['admin_password']
        admin = Admin.query.filter_by(username=username).first()

        if admin:
            if check_password_hash(admin.password, admin_password):
                login_user(admin)
                return redirect(url_for('admin.account'))
            else:
                return render_template('admin/login.html', errors='Incorrect Password')
        return render_template('admin/login.html', errors='Admin does not exist')

    elif request.method == 'GET':
        return render_template('admin/login.html')


@admins_blueprint.route('/admin-account', methods=['GET','POST'])
@login_required
def account():
    try:
        if request.method == 'POST':
            subscription = request.form["subscriptions"]
            username = request.form["username"]

            if subscription == "None":
                obj = Users.query.all()
                return render_template('admin/account.html', users=obj, errors="Please enter a valid subscription value")

            user = Users.query.filter_by(insta_username=username).first_or_404()
            user.subscription_plan = subscription
            user.from_date = datetime.datetime.now()
            user.till_date = datetime.datetime.now() + timedelta(days=int(subscription))
            user.is_subscribed = True
            db.session.commit()

        obj = Users.query.all()
        return render_template('admin/account.html', users=obj, is_admin=True)

    except:
        if request.method == 'POST':
            insta_username = request.form["search"]
            users = Users.query.filter(Users.insta_username.like("%{}%".format(insta_username))).all()
            return render_template('admin/account.html', users=users, is_admin=True)

        obj = Users.query.all()
        return render_template('admin/account.html', users=obj, is_admin=True)



@login_required
@admins_blueprint.route('/admin_logout')
def logout():
    logout_user()
    return redirect(url_for('core.index'))