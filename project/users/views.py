import sys
import datetime
from project import app
from common_utilities import Constant
from project.users.models import Counter, Users
from flask_login import login_required, logout_user, current_user
from flask import Blueprint, render_template, session, make_response, jsonify, request, redirect, url_for

sys.path.append('../../')
from project.users.memcache_ctrl import client, CONSTANT


users_blueprint = Blueprint('users', __name__, template_folder='templates')

@users_blueprint.route('/request_accepted_counter', methods=['GET', 'POST'])
@login_required
def request_accepted_counter():
    if request.method == "POST":
        instagram_username = session.get("username").get("username")
        counter_id = session.get("current_counter_id")
        if counter_id is None:
            counter_id_obj = Counter().get_last_counter_info(instagram_username)
            if counter_id_obj is not None:
                counter_id = counter_id_obj.id
                session["current_counter_id"] = counter_id_obj.id
                session.modified = True

        total_success_request, total_request, failed_request = 0, 0, 0
        is_complete = False
        last_date_time = None
        try:
            dict_index_name = instagram_username.lower() + CONSTANT.ALL_INFO.value
            all_info = client.get(dict_index_name)
            if isinstance(all_info, dict):
                total_request = all_info[CONSTANT.TOTAL_REQUEST_TO_BE_ACCEPT.value]
                total_success_request = all_info[CONSTANT.SUCCESSFUL_ACCEPTED.value]
                failed_request = all_info[CONSTANT.REQUEST_FAILED.value]
                is_complete = all_info[CONSTANT.IS_REQUEST_COMPLETE.value]
                if is_complete == True:
                    last_date_time = all_info.get("update_date")
            else:
                counter_stats_row = Counter.get_one_counter(counter_id)
                if counter_stats_row is not None:
                    total_success_request = counter_stats_row.total_accepted_request
                    total_request = counter_stats_row.input_request_count
                    failed_request = counter_stats_row.input_request_count
                    is_complete = counter_stats_row.is_request_complete
                    last_date_time = counter_stats_row.update_date

        except Exception as error:
            print("Not able to get count ", error)

        response_dict = {"successful": total_success_request,
                         "username": instagram_username.upper(),
                         "failed": failed_request,
                         "isComplete": is_complete,
                         "total": total_request,
                         "lastDateTime": last_date_time.strftime("%a %B %d %Y %I:%M:%S %p") if last_date_time is not None else None}
        return make_response(jsonify(response_dict), 200)


@users_blueprint.route('/accept_pending_requests', methods=["GET", "POST"])
@login_required
def accept():
    if request.method == "POST":
        instagram_username = session["username"]["username"]
        bot_obj = client.get(instagram_username)["bot_obj"]
        no_to_accept = request.form.get("customUserInputNumber", 0)

        init_dict_items = {
            Constant.CONSTANT.TOTAL_REQUEST_TO_BE_ACCEPT.value: no_to_accept,
            Constant.CONSTANT.IS_REQUEST_COMPLETE.value: False,
            Constant.CONSTANT.SUCCESSFUL_ACCEPTED.value: 0,
            Constant.CONSTANT.REQUEST_FAILED.value: 0,
        }

        dict_get_index = instagram_username.lower() + Constant.CONSTANT.ALL_INFO.value

        client.set(dict_get_index, init_dict_items)
        new_user_count_req = Counter(
            insta_username=instagram_username,
            input_request_count=no_to_accept,
            total_accepted_request=0,
            total_failed_request=0
        )
        new_user_count_req.save()

        counter_id = new_user_count_req.id
        session["current_counter_id"] = counter_id
        session.modified = True

        ctr_item = Counter.get_one_counter(session["current_counter_id"])
        resp = bot_obj.approve_pending_follow_requests(number_of_requests=int(no_to_accept), ctr_item=ctr_item, init_dict_items=init_dict_items, dict_get_index=dict_get_index, counter_ctr=0)

        if resp == "No request to accept":
            return "No request to accept"

        if resp == None:
            return "True"
        return "True"

    elif request.method == "GET":
        instagram_username = session.get("username").get("username")
        user_obj = Users.query.filter_by(insta_username=instagram_username).first()
        last_day = str(days_between(user_obj.till_date)) + " days"
        return render_template("AcceptRequests.html", last_day=last_day)


@users_blueprint.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    try:
        instagram_username = current_user.insta_username
        if current_user.is_authenticated():
            client.delete(instagram_username)
        logout_user()
    except:
        pass
    return redirect(url_for('core.index'))

def days_between(d1):
    d1 = datetime.datetime.strptime(str(d1.date()), "%Y-%m-%d")
    d2 = datetime.datetime.strptime(str(datetime.datetime.utcnow().date()), "%Y-%m-%d")
    return abs((d2 - d1).days)


default_args = {}
footer_var = {"cp_year": datetime.datetime.now().year}


@app.before_first_request
def load_default():
    default_args["footer_content"] = render_template("footer.html", **footer_var)
    return default_args