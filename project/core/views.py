import datetime
from project import app, bot
from project.users.models import Users
from project.users.memcache_ctrl import client
from project.users.memcache_ctrl import CONSTANT
from common_utilities.login_mappings import mappings
from common_utilities.subscription import check_subscription
from flask_login import login_user, current_user, logout_user
from flask import render_template, Blueprint, request, url_for, redirect, session


core_blueprint = Blueprint('core', __name__, template_folder='templates', static_folder='static')


@core_blueprint.route('/', methods=['GET','POST'])
def index():
    if request.method == "POST":
        instagram_username = request.form['userEmailID']
        instagram_password = request.form['userLoginPassword']
        instagram_username = instagram_username.lower()
        session["username"] = {}
        session["username"]["singleton"] = True
        session["username"]["username"] = instagram_username
        session["counter_id"] = instagram_username + CONSTANT.ALL_INFO.value

        is_subscription_check = check_subscription(instagram_username)
        if not is_subscription_check:
            session["message"] = "Please subscribe to login"
            return redirect(url_for('core.pricing'))

        global bot_obj
        bot_obj = bot()
        resp = bot_obj.login(username=instagram_username, password=instagram_password, ask_for_code=True)
        cl_obj = client.get(instagram_username)

        if cl_obj.get("bot_obj"):
            client.set(instagram_username, cl_obj)
        else:
            cl_obj["bot_obj"] = bot_obj
            client.set(instagram_username, cl_obj)

        if resp == "906":
            return redirect(url_for('core.verify_code'))

        if resp != True:
            return render_template("index.html", page="index", errors=mappings[resp], **default_args)
        else:
            user = Users.query.filter_by(insta_username=instagram_username).first()
            login_user(user=user)
            print(user.is_authenticated())
            return redirect(url_for('users.accept'))

    elif request.method == "GET":
        try:
            if current_user.is_authenticated:
                instagram_username = current_user.insta_username
                client.delete(instagram_username)
                logout_user()
        except:
            pass
        return render_template('index.html', page="index", errors=[], **default_args, current_user=current_user)


@core_blueprint.route('/verify-code', methods=["GET", "POST"])
def verify_code():
    if request.method == "POST":
        code = request.form['userLoginPassword']
        instagram_username = session["username"]["username"]

        cl_obj = client.get(instagram_username)
        api_obj = cl_obj["api"]

        resp = api_obj.two_factor_auth_remodified(code, api_obj)

        if resp:
            import time
            api_obj.is_logged_in = True
            api_obj.last_login = time.time()
            client.set(instagram_username, cl_obj)
            resp2 = api_obj.login_flow(True)

            if resp2:
                user = Users.query.filter_by(insta_username=instagram_username).first()
                login_user(user=user)
                return redirect(url_for('users.accept'))
            else:
                return render_template("index.html", page="index", errors="Wrong Code", **default_args)
        else:
            return render_template("index.html", page="index", errors="Wrong Code", **default_args)


    elif request.method == "GET":
        return render_template('verify_code.html')


@core_blueprint.route('/pricing')
def pricing():
    return render_template('Pricing.html', **default_args)


@core_blueprint.route('/faq')
def faq():
    return render_template('FAQ.html', **default_args)


@core_blueprint.route('/contact')
def contact():
    return render_template('Contact.html', **default_args)


default_args = {}
footer_var = {"cp_year":datetime.datetime.now().year}
@app.before_first_request
def load_default():
    default_args["footer_content"] = render_template("footer.html", **footer_var)
    return default_args