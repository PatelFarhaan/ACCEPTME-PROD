import os
import rsa
import hmac
import json
import sys
import time
import uuid
import base64
import random
import secrets
import hashlib
import datetime
import requests
import requests.utils
from . import config, devices
import six.moves.urllib as urllib
from Crypto.PublicKey import RSA
from Cryptodome.Cipher import AES

from .api_login import (
    change_device_simulation,
    generate_all_uuids,
    login_flow,
    pre_login_flow,
    reinstall_app_simulation,
    set_device,
    sync_launcher,
    get_prefill_candidates,
    get_account_family,
    get_zr_token_result,
    banyan,
    igtv_browse_feed,
    sync_device_features,
    creatives_ar_class,
    set_contact_point_prefill,
)

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


version_info = sys.version_info[0:3]
is_py2 = version_info[0] == 2
is_py3 = version_info[0] == 3
is_py37 = version_info[:2] == (3, 7)


version = "1.0.0"
current_path = os.path.abspath(os.getcwd())


class API(object):
    def __init__(
            self,
            device=None,
            save_logfile=True,
            log_filename=None,
    ):
        self.device = device or devices.DEFAULT_DEVICE

        self.cookie_fname = None
        self.session = requests.Session()  # new line of code

        self.is_logged_in = False
        self.last_login = None

        self.last_response = None
        self.total_requests = 0



    def set_user(self, username, password, generate_all_uuids=True, set_device=True):
        self.username = username
        self.password = password

        if set_device is True:
            self.set_device()

        if generate_all_uuids is True:
            self.generate_all_uuids()

    def get_suggested_searches(self, _type="users"):
        return self.send_request(
            "fbsearch/suggested_searches/", self.json_data({"type": _type})
        )

    def read_msisdn_header(self, usage="default"):
        data = json.dumps({"device_id": self.uuid, "mobile_subno_usage": usage})
        return self.send_request(
            "accounts/read_msisdn_header/",
            data,
            login=True,
            headers={"X-DEVICE-ID": self.uuid},
        )

    def log_attribution(self, usage="default"):
        data = json.dumps({"adid": self.advertising_id})
        return self.send_request("attribution/log_attribution/", data, login=True)

    # ====== ALL METHODS IMPORT FROM api_login ====== #
    def sync_device_features(self, login=None):
        return sync_device_features(self, login)

    def sync_launcher(self, login=None):
        return sync_launcher(self, login)

    def set_contact_point_prefill(self, usage=None, login=False):
        return set_contact_point_prefill(self, usage, login)

    def igtv_browse_feed(self):
        return igtv_browse_feed(self)

    def creatives_ar_class(self):
        return creatives_ar_class(self)

    def get_prefill_candidates(self, login=False):
        return get_prefill_candidates(self, login)

    def get_account_family(self):
        return get_account_family(self)

    def get_zr_token_result(self):
        return get_zr_token_result(self)

    def banyan(self):
        return banyan(self)

    def pre_login_flow(self):
        return pre_login_flow(self)

    def login_flow(self, just_logged_in=False, app_refresh_interval=1800):
        return login_flow(self, just_logged_in, app_refresh_interval)

    def set_device(self):
        return set_device(self)

    def generate_all_uuids(self):
        return generate_all_uuids(self)

    def reinstall_app_simulation(self):
        return reinstall_app_simulation(self)

    def change_device_simulation(self):
        return change_device_simulation(self)

    def encrypt_password(self, password):
        IG_LOGIN_ANDROID_PUBLIC_KEY = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF1enRZOEZvUlRGRU9mK1RkTGlUdAplN3FIQXY1cmdBMmk5RkQ0YjgzZk1GK3hheW14b0xSdU5KTitRanJ3dnBuSm1LQ0QxNGd3K2w3TGQ0RHkvRHVFCkRiZlpKcmRRWkJIT3drS3RqdDdkNWlhZFdOSjdLczlBM0NNbzB5UktyZFBGU1dsS21lQVJsTlFrVXF0YkNmTzcKT2phY3ZYV2dJcGlqTkdJRVk4UkdzRWJWZmdxSmsrZzhuQWZiT0xjNmEwbTMxckJWZUJ6Z0hkYWExeFNKOGJHcQplbG4zbWh4WDU2cmpTOG5LZGk4MzRZSlNaV3VxUHZmWWUrbEV6Nk5laU1FMEo3dE80eWxmeWlPQ05ycnF3SnJnCjBXWTFEeDd4MHlZajdrN1NkUWVLVUVaZ3FjNUFuVitjNUQ2SjJTSTlGMnNoZWxGNWVvZjJOYkl2TmFNakpSRDgKb1FJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=="
        IG_LOGIN_ANDROID_PUBLIC_KEY_ID = 205

        key = secrets.token_bytes(32)
        iv = secrets.token_bytes(12)
        time = str(int(datetime.datetime.now().timestamp()))

        base64_decoded_device_public_key = base64.b64decode(
            IG_LOGIN_ANDROID_PUBLIC_KEY.encode()
        )

        public_key = RSA.importKey(base64_decoded_device_public_key)

        encrypted_aes_key = rsa.encrypt(key, public_key)

        cipher = AES.new(key, AES.MODE_GCM, iv)
        cipher.update(time.encode())
        encrypted_password, tag = cipher.encrypt_and_digest(password.encode())

        payload = (
                b"\x01"
                + str(IG_LOGIN_ANDROID_PUBLIC_KEY_ID).encode()
                + iv
                + b"0001"
                + encrypted_aes_key
                + tag
                + encrypted_password
        )

        base64_encoded_payload = base64.b64encode(payload)

        return f"#PWD_INSTAGRAM:4:{time}:{base64_encoded_payload.decode()}"

    def login(
            self,
            username=None,
            password=None,
            force=False,
            proxy=None,
            use_cookie=True,
            use_uuid=True,
            cookie_fname=None,
            ask_for_code=False,
            set_device=True,
            generate_all_uuids=True,
            is_threaded=False,
    ):

        set_device = generate_all_uuids = True
        self.set_user(username, password)
        # self.session = requests.Session()

        # import sys
        # sys.path.append("../../")
        # from project.users.memcache_ctrl import client
        # cl_obj = client.get(username)
        # cl_obj["session"] = self.session
        # client.set(username, cl_obj)

        self.proxy = proxy
        self.set_proxy()  # Only happens if `self.proxy`

        cookie_is_loaded = False
        msg = "Login flow failed, the cookie is broken. Relogin again."

        if not cookie_is_loaded and (not self.is_logged_in or force):
            # self.session = requests.Session()
            self.pre_login_flow()
            data = json.dumps(
                {
                    "jazoest": str(random.randint(22000, 22999)),
                    "country_codes": '[{"country_code":"1","source":["default"]}]',
                    "phone_id": self.phone_id,
                    "_csrftoken": self.token,
                    "username": self.username,
                    "adid": "",
                    "guid": self.uuid,
                    "device_id": self.device_id,
                    "google_tokens": "[]",
                    "password": self.password,
                    "login_attempt_count": "1",
                }
            )

            res = self.send_request("accounts/login/", data, True)
            if res == "906":
                return "906"
            elif res:
                self.save_successful_login()
                self.login_flow(True)
                return True

            elif self.last_json.get("error_type", "") == "checkpoint_challenge_required":
                return "905"

            elif self.last_json.get("two_factor_required"):
                return "903"

            else:
                return "904"

    def two_factor_auth(self):
        # import sys
        # sys.path.append("../../")
        # from project.users.memcache_ctrl import client
        # cl_obj = client.get(self.username)
        # cl_obj["bots_obj"] = self
        # cl_obj["session"] = self.session
        # client.set(self.username, cl_obj)
        return "906"
        # two_factor_code = input("Enter 2FA verification code: ")
        # two_factor_id = self.last_json["two_factor_info"]["two_factor_identifier"]
        #
        # login = self.session.post(
        #     config.API_URL + "accounts/two_factor_login/",
        #     data={
        #         "username": self.username,
        #         "verification_code": two_factor_code,
        #         "two_factor_identifier": two_factor_id,
        #         "password": self.password,
        #         "device_id": self.device_id,
        #         "ig_sig_key_version": config.SIG_KEY_VERSION,
        #     },
        #     allow_redirects=True,
        #     )
        #
        # if login.status_code == 200:
        #     resp_json = json.loads(login.text)
        #     if resp_json["status"] != "ok":
        #         return False
        #     return True
        # else:
        #     return False

    def two_factor_auth_remodified(self, two_factor_code, api_obj):
        two_factor_id = api_obj.last_json["two_factor_info"]["two_factor_identifier"]

        self.session = api_obj.session

        login = self.session.post(
            config.API_URL + "accounts/two_factor_login/",
            data={
                "username": api_obj.username,
                "verification_code": two_factor_code,
                "two_factor_identifier": two_factor_id,
                "password": api_obj.password,
                "device_id": api_obj.device_id,
                "ig_sig_key_version": config.SIG_KEY_VERSION,
            },
            allow_redirects=True,
            )

        print(login.text)

        if login.status_code == 200:
            resp_json = json.loads(login.text)
            if resp_json["status"] != "ok":
                return False
            return True
        else:
            return False

    def save_successful_login(self):
        self.is_logged_in = True
        self.last_login = time.time()

    def save_failed_login(self):
        # self.logger.info("Username or password is incorrect.")
        # delete_credentials()
        sys.exit()

    def solve_challenge(self):
        challenge_url = self.last_json["challenge"]["api_path"][1:]
        try:
            self.send_request(challenge_url, None, login=True, with_signature=False)
        except Exception as e:
            return False

        choices = self.get_challenge_choices()
        for choice in choices:
            print(choice)
        code = input("Insert choice: ")

        data = json.dumps({"choice": code})
        try:
            self.send_request(challenge_url, data, login=True)
        except Exception as e:
            return False

        print("A code has been sent to the method selected, please check.")
        code = input("Insert code: ").replace(" ", "")

        data = json.dumps({"security_code": code})
        try:
            self.send_request(challenge_url, data, login=True)
        except Exception as e:
            return False


        worked = (
                ("logged_in_user" in self.last_json)
                and (self.last_json.get("action", "") == "close")
                and (self.last_json.get("status", "") == "ok")
        )

        if worked:
            return True
        return False

    def get_challenge_choices(self):
        last_json = self.last_json
        choices = []

        if last_json.get("step_name", "") == "select_verify_method":
            choices.append("Checkpoint challenge received")
            if "phone_number" in last_json["step_data"]:
                choices.append("0 - Phone")
            if "email" in last_json["step_data"]:
                choices.append("1 - Email")

        if last_json.get("step_name", "") == "delta_login_review":
            choices.append("Login attempt challenge received")
            choices.append("0 - It was me")
            choices.append("0 - It wasn't me")

        if not choices:
            choices.append(
                '"{}" challenge received'.format(last_json.get("step_name", "Unknown"))
            )
            choices.append("0 - Default")

        return choices

    def logout(self, *args, **kwargs):
        if not self.is_logged_in:
            return True
        data = json.dumps({})
        self.is_logged_in = not self.send_request(
            "accounts/logout/", data, with_signature=False
        )
        return not self.is_logged_in

    def set_proxy(self):
        if getattr(self, "proxy", None):
            parsed = urllib.parse.urlparse(self.proxy)
            scheme = "http://" if not parsed.scheme else ""
            self.session.proxies["http"] = scheme + self.proxy
            self.session.proxies["https"] = scheme + self.proxy

    def send_request(
            self,
            endpoint,
            post=None,
            login=False,
            with_signature=True,
            headers=None,
            extra_sig=None,
            timeout_minutes=None):
        self.set_proxy()  # Only happens if `self.proxy`
        # TODO: fix the request_headers
        # import sys
        # sys.path.append("../../")
        # from project.users.memcache_ctrl import client
        #
        # cl_obj = client.get(self.username)
        # if cl_obj.get("session"):
        #     if not self.session == cl_obj["session"]:
        #         cl_obj["session"].headers.update(self.session.headers)
        #         cl_obj["session"].cookies.update(self.session.cookies)
        #         client.set(self.username, cl_obj)
        #     self.session = cl_obj["session"]
        # else:
        #     cl_obj["session"] = self.session
        #     client.set(self.username, cl_obj)

        self.session.headers.update(config.REQUEST_HEADERS)
        self.session.headers.update({"User-Agent": self.user_agent})

        # cl_obj = client.get(self.username)
        # if cl_obj.get("session"):
        #     if not self.session == cl_obj["session"]:
        #         cl_obj["session"].headers.update(self.session.headers)
        #         cl_obj["session"].cookies.update(self.session.cookies)
        #         client.set(self.username, cl_obj)
        #     self.session = cl_obj["session"]


        if not self.is_logged_in and not login:
            msg = "Not logged in!"
            raise Exception(msg)
        try:
            self.total_requests += 1
            if post is not None:
                if with_signature:
                    post = self.generate_signature(post)
                    if extra_sig is not None and extra_sig != []:
                        post += "&".join(extra_sig)

                response = self.session.post(config.API_URL + endpoint, data=post)
            else:
                response = self.session.get(config.API_URL + endpoint)

        except Exception as e:
            return False

        self.last_response = response

        if response.status_code == 200:
            try:
                self.last_json = json.loads(response.text)
                return True
            except JSONDecodeError:
                return False
        else:
            if response.status_code != 404 and response.status_code != "404":
                pass
            try:
                response_data = json.loads(response.text)
                if response_data.get(
                        "message"
                ) is not None and "feedback_required" in str(
                    response_data.get("message").encode("utf-8")
                ):
                    try:
                        self.last_response = response
                        self.last_json = json.loads(response.text)
                    except Exception:
                        pass
                    return "feedback_required"
            except ValueError:
                pass
            if response.status_code == 429:
                if timeout_minutes is None:
                    timeout_minutes = 0
                if timeout_minutes == 15:
                    time.sleep(1)
                    sys.exit()
                timeout_minutes += 5
                time.sleep(timeout_minutes * 60)
                return self.send_request(
                    endpoint,
                    post,
                    login,
                    with_signature,
                    headers,
                    extra_sig,
                    timeout_minutes,
                )
            if response.status_code == 400:
                response_data = json.loads(response.text)
                if response_data.get("challenge_required"):
                    pass
                if response_data.get("two_factor_required"):
                    try:
                        self.last_response = response
                        self.last_json = json.loads(response.text)
                    except Exception:
                        pass
                    return self.two_factor_auth()

            try:
                self.last_response = response
                self.last_json = json.loads(response.text)
            except Exception:
                pass
            return False

    @property
    def cookie_dict(self):
        return self.session.cookies.get_dict()

    @property
    def token(self):
        return self.cookie_dict["csrftoken"]

    @property
    def user_id(self):
        return self.cookie_dict["ds_user_id"]

    @property
    def mid(self):
        return self.cookie_dict["mid"]

    @property
    def sessionid(self):
        return self.cookie_dict["sessionid"]

    @property
    def views(self):
        return self.cookie_dict["views"]

    @property
    def rank_token(self):
        return "{}_{}".format(self.user_id, self.uuid)

    @property
    def default_data(self):
        return {"_uuid": self.uuid, "_uid": self.user_id, "_csrftoken": self.token}

    def json_data(self, data=None):
        """Adds the default_data to data and dumps it to a json."""
        if data is None:
            data = {}
        data.update(self.default_data)
        return json.dumps(data)

    def action_data(self, data):
        _data = {"radio_type": "wifi-none", "device_id": self.device_id}
        data.update(_data)
        return data

    def auto_complete_user_list(self):
        return self.send_request("friendships/autocomplete_user_list/")

    def batch_fetch(self):
        data = {
            "surfaces_to_triggers": '{"4715":["instagram_feed_header"],"5858":["instagram_feed_tool_tip"],"5734":["instagram_feed_prompt"]}',  # noqa
            "surfaces_to_queries": '{"4715":"Query+QuickPromotionSurfaceQuery:+Viewer+{viewer()+{eligible_promotions.trigger_context_v2(<trigger_context_v2>).ig_parameters(<ig_parameters>).trigger_name(<trigger_name>).surface_nux_id(<surface>).external_gating_permitted_qps(<external_gating_permitted_qps>).supports_client_filters(true).include_holdouts(true)+{edges+{client_ttl_seconds,log_eligibility_waterfall,is_holdout,priority,time_range+{start,end},node+{id,promotion_id,logging_data,max_impressions,triggers,contextual_filters+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}}}}}},is_uncancelable,template+{name,parameters+{name,required,bool_value,string_value,color_value,}},creatives+{title+{text},content+{text},footer+{text},social_context+{text},social_context_images,primary_action{title+{text},url,limit,dismiss_promotion},secondary_action{title+{text},url,limit,dismiss_promotion},dismiss_action{title+{text},url,limit,dismiss_promotion},image.scale(<scale>)+{uri,width,height}}}}}}}","5858":"Query+QuickPromotionSurfaceQuery:+Viewer+{viewer()+{eligible_promotions.trigger_context_v2(<trigger_context_v2>).ig_parameters(<ig_parameters>).trigger_name(<trigger_name>).surface_nux_id(<surface>).external_gating_permitted_qps(<external_gating_permitted_qps>).supports_client_filters(true).include_holdouts(true)+{edges+{client_ttl_seconds,log_eligibility_waterfall,is_holdout,priority,time_range+{start,end},node+{id,promotion_id,logging_data,max_impressions,triggers,contextual_filters+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}}}}}},is_uncancelable,template+{name,parameters+{name,required,bool_value,string_value,color_value,}},creatives+{title+{text},content+{text},footer+{text},social_context+{text},social_context_images,primary_action{title+{text},url,limit,dismiss_promotion},secondary_action{title+{text},url,limit,dismiss_promotion},dismiss_action{title+{text},url,limit,dismiss_promotion},image.scale(<scale>)+{uri,width,height}}}}}}}","5734":"Query+QuickPromotionSurfaceQuery:+Viewer+{viewer()+{eligible_promotions.trigger_context_v2(<trigger_context_v2>).ig_parameters(<ig_parameters>).trigger_name(<trigger_name>).surface_nux_id(<surface>).external_gating_permitted_qps(<external_gating_permitted_qps>).supports_client_filters(true).include_holdouts(true)+{edges+{client_ttl_seconds,log_eligibility_waterfall,is_holdout,priority,time_range+{start,end},node+{id,promotion_id,logging_data,max_impressions,triggers,contextual_filters+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}},clauses+{clause_type,filters+{filter_type,unknown_action,value+{name,required,bool_value,int_value,string_value},extra_datas+{name,required,bool_value,int_value,string_value}}}}}},is_uncancelable,template+{name,parameters+{name,required,bool_value,string_value,color_value,}},creatives+{title+{text},content+{text},footer+{text},social_context+{text},social_context_images,primary_action{title+{text},url,limit,dismiss_promotion},secondary_action{title+{text},url,limit,dismiss_promotion},dismiss_action{title+{text},url,limit,dismiss_promotion},image.scale(<scale>)+{uri,width,height}}}}}}}"}',
            "vc_policy": "default",
            "_csrftoken": self.token,
            "_uid": self.user_id,
            "_uuid": self.uuid,
            "scale": 2,
            "version": 1,
        }
        data = self.json_data(data)
        return self.send_request("qp/batch_fetch/", data)

    def get_timeline_feed(self, reason=None, options=[]):
        headers = {
            "X-Ads-Opt-Out": "0",
            # "X-DEVICE-ID": self.uuid,
            # "X-CM-Bandwidth-KBPS": str(random.randint(2000, 5000)),
            # "X-CM-Latency": str(random.randint(1, 5)),
        }
        data = {
            "feed_view_info": "[]",
            "phone_id": self.phone_id,
            "battery_level": random.randint(25, 100),
            # "timezone_offset": datetime.datetime.now(pytz.timezone("CET")).strftime(
            #    "%z"
            # ),
            "timezone_offset": "0",
            "_csrftoken": self.token,
            "device_id": self.uuid,
            "request_id": self.uuid,
            "_uuid": self.uuid,
            "is_charging": random.randint(0, 1),
            "will_sound_on": random.randint(0, 1),
            "session_id": self.client_session_id,
            "bloks_versioning_id": "e538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88e",
        }

        if "is_pull_to_refresh" in options:
            data["reason"] = "pull_to_refresh"
            data["is_pull_to_refresh"] = "1"
        elif "is_pull_to_refresh" not in options:
            data["reason"] = "cold_start_fetch"
            data["is_pull_to_refresh"] = "0"

        if "push_disabled" in options:
            data["push_disabled"] = "true"

        if "recovered_from_crash" in options:
            data["recovered_from_crash"] = "1"

        data = json.dumps(data)
        return self.send_request(
            "feed/timeline/", data, with_signature=False, headers=headers
        )

    def get_megaphone_log(self):
        return self.send_request("megaphone/log/")

    def expose(self):
        data = self.json_data(
            {"id": self.uuid, "experiment": "ig_android_profile_contextual_feed"}
        )
        return self.send_request("qe/expose/", data)



    # ====== MEDIA METHODS ====== #
    def edit_media(self, media_id, captionText=""):
        data = self.json_data({"caption_text": captionText})
        url = "media/{media_id}/edit_media/".format(media_id=media_id)
        return self.send_request(url, data)

    def remove_self_tag(self, media_id):
        data = self.json_data()
        url = "media/{media_id}/remove/".format(media_id=media_id)
        return self.send_request(url, data)

    def media_info(self, media_id):
        # data = self.json_data({'media_id': media_id})
        url = "media/{media_id}/info/".format(media_id=media_id)
        return self.send_request(url)

    def archive_media(self, media, undo=False):
        action = "only_me" if not undo else "undo_only_me"
        data = self.json_data({"media_id": media["id"]})
        url = "media/{media_id}/{action}/?media_type={media_type}".format(
            media_id=media["id"], action=action, media_type=media["media_type"]
        )
        return self.send_request(url, data)

    def delete_media(self, media):
        data = self.json_data({"media_id": media.get("id")})
        url = "media/{media_id}/delete/".format(media_id=media.get("id"))
        return self.send_request(url, data)

    def gen_user_breadcrumb(self, size):
        key = "iN4$aGr0m"
        dt = int(time.time() * 1000)

        time_elapsed = random.randint(500, 1500) + size * random.randint(500, 1500)
        text_change_event_count = max(1, size / random.randint(3, 5))

        data = "{size!s} {elapsed!s} {count!s} {dt!s}".format(
            **{
                "size": size,
                "elapsed": time_elapsed,
                "count": text_change_event_count,
                "dt": dt,
            }
        )
        return "{!s}\n{!s}\n".format(
            base64.b64encode(
                hmac.new(
                    key.encode("ascii"), data.encode("ascii"), digestmod=hashlib.sha256
                ).digest()
            ),
            base64.b64encode(data.encode("ascii")),
        )

    def comment(self, media_id, comment_text):
        return self.send_request(
            endpoint="media/{media_id}/comment/".format(media_id=media_id),
            post=self.json_data(
                self.action_data(
                    {
                        "container_module": "comments_v2",
                        "user_breadcrumb": self.gen_user_breadcrumb(len(comment_text)),
                        "idempotence_token": self.generate_UUID(True),
                        "comment_text": comment_text,
                    }
                )
            ),
        )

    def reply_to_comment(self, media_id, comment_text, parent_comment_id):
        data = self.json_data(
            {"comment_text": comment_text, "replied_to_comment_id": parent_comment_id}
        )
        url = "media/{media_id}/comment/".format(media_id=media_id)
        return self.send_request(url, data)

    def delete_comment(self, media_id, comment_id):
        data = self.json_data()
        url = "media/{media_id}/comment/{comment_id}/delete/"
        url = url.format(media_id=media_id, comment_id=comment_id)
        return self.send_request(url, data)

    def get_comment_likers(self, comment_id):
        url = "media/{comment_id}/comment_likers/?".format(comment_id=comment_id)
        return self.send_request(url)

    def get_media_likers(self, media_id):
        url = "media/{media_id}/likers/?".format(media_id=media_id)
        return self.send_request(url)

    def like_comment(self, comment_id):
        data = self.json_data(
            {
                "is_carousel_bumped_post": "false",
                "container_module": "comments_v2",
                "feed_position": "0",
            }
        )
        url = "media/{comment_id}/comment_like/".format(comment_id=comment_id)
        return self.send_request(url, data)

    def unlike_comment(self, comment_id):
        data = self.json_data(
            {
                "is_carousel_bumped_post": "false",
                "container_module": "comments_v2",
                "feed_position": "0",
            }
        )
        url = "media/{comment_id}/comment_unlike/".format(comment_id=comment_id)
        return self.send_request(url, data)

    # From profile => "is_carousel_bumped_post":"false",
    # "container_module":"feed_contextual_profile", "feed_position":"0" # noqa
    # From home/feed => "inventory_source":"media_or_ad",
    # "is_carousel_bumped_post":"false", "container_module":"feed_timeline",
    # "feed_position":"0" # noqa
    def like(
            self,
            media_id,
            double_tap=None,
            container_module="feed_short_url",
            feed_position=0,
            username=None,
            user_id=None,
            hashtag_name=None,
            hashtag_id=None,
            entity_page_name=None,
            entity_page_id=None,
    ):
        data = self.action_data(
            {
                "inventory_source": "media_or_ad",
                "media_id": media_id,
                "_csrftoken": self.token,
                "radio_type": "wifi-none",
                "_uid": self.user_id,
                "_uuid": self.uuid,
                "is_carousel_bumped_post": "false",
                "container_module": container_module,
                "feed_position": str(feed_position),
            }
        )
        if container_module == "feed_timeline":
            data.update({"inventory_source": "media_or_ad"})
        if username:
            data.update({"username": username, "user_id": user_id})
        if hashtag_name:
            data.update({"hashtag_name": hashtag_name, "hashtag_id": hashtag_id})
        if entity_page_name:
            data.update(
                {"entity_page_name": entity_page_name, "entity_page_id": entity_page_id}
            )
        # if double_tap is None:
        double_tap = random.randint(0, 1)
        json_data = self.json_data(data)
        # TODO: comment out debug log out when done
        self.logger.debug("post data: {}".format(json_data))
        return self.send_request(
            endpoint="media/{media_id}/like/".format(media_id=media_id),
            post=json_data,
            extra_sig=["d={}".format(double_tap)],
        )

    def unlike(self, media_id):
        data = self.json_data(
            {
                "media_id": media_id,
                "radio_type": "wifi-none",
                "is_carousel_bumped_post": "false",
                "container_module": "photo_view_other",
                "feed_position": "0",
            }
        )
        url = "media/{media_id}/unlike/".format(media_id=media_id)
        return self.send_request(url, data)

    def get_media_comments(self, media_id, max_id=""):
        url = "media/{media_id}/comments/".format(media_id=media_id)
        if max_id:
            url += "?max_id={max_id}".format(max_id=max_id)
        return self.send_request(url)


    def get_username_info(self, user_id):
        url = "users/{user_id}/info/".format(user_id=user_id)
        return self.send_request(url)

    def get_self_username_info(self):
        return self.get_username_info(self.user_id)

    def get_news_inbox(self):
        return self.send_request("news/inbox/")

    def get_recent_activity(self):
        return self.send_request("news/inbox/?limited_activity=true&show_su=true")

    def get_following_recent_activity(self):
        return self.send_request("news")

    def get_user_tags(self, user_id):
        url = (
            "usertags/{user_id}/feed/?rank_token=" "{rank_token}&ranked_content=true&"
        ).format(user_id=user_id, rank_token=self.rank_token)
        return self.send_request(url)

    def get_self_user_tags(self):
        return self.get_user_tags(self.user_id)

    def get_geo_media(self, user_id):
        url = "maps/user/{user_id}/".format(user_id=user_id)
        return self.send_request(url)

    def get_self_geo_media(self):
        return self.get_geo_media(self.user_id)

    def sync_from_adress_book(self, contacts):
        url = "address_book/link/?include=extra_display_name,thumbnails"
        return self.send_request(url, "contacts=" + json.dumps(contacts))

    # ====== FEED METHODS ====== #
    def tag_feed(self, tag):
        url = "feed/tag/{tag}/?rank_token={rank_token}&ranked_content=true&"
        return self.send_request(url.format(tag=tag, rank_token=self.rank_token))

    def get_timeline(self):
        url = "feed/timeline/?rank_token={rank_token}&ranked_content=true&"
        return self.send_request(url.format(rank_token=self.rank_token))

    def get_archive_feed(self):
        url = "feed/only_me_feed/?rank_token={rank_token}&ranked_content=true&"
        return self.send_request(url.format(rank_token=self.rank_token))

    def get_user_feed(self, user_id, max_id="", min_timestamp=None):
        url = (
            "feed/user/{user_id}/?max_id={max_id}&min_timestamp="
            "{min_timestamp}&rank_token={rank_token}&ranked_content=true"
            # noqa
        ).format(
            user_id=user_id,
            max_id=max_id,
            min_timestamp=min_timestamp,
            rank_token=self.rank_token,
        )
        return self.send_request(url)

    def get_self_user_feed(self, max_id="", min_timestamp=None):
        return self.get_user_feed(self.user_id, max_id, min_timestamp)

    def get_hashtag_feed(self, hashtag, max_id=""):
        url = (
            "feed/tag/{hashtag}/?max_id={max_id}"
            "&rank_token={rank_token}&ranked_content=true&"
        ).format(hashtag=hashtag, max_id=max_id, rank_token=self.rank_token)
        return self.send_request(url)

    def get_location_feed(self, location_id, max_id=""):
        url = (
            "feed/location/{location_id}/?max_id={max_id}"
            "&rank_token={rank_token}&ranked_content=true&"
        ).format(location_id=location_id, max_id=max_id, rank_token=self.rank_token)
        return self.send_request(url)

    def get_popular_feed(self):
        url = (
            "feed/popular/?people_teaser_supported=1"
            "&rank_token={rank_token}&ranked_content=true&"
        )
        return self.send_request(url.format(rank_token=self.rank_token))

    def get_liked_media(self, max_id=""):
        url = "feed/liked/?max_id={max_id}".format(max_id=max_id)
        return self.send_request(url)

    # ====== FRIENDSHIPS METHODS ====== #
    def get_user_followings(self, user_id, max_id=""):
        url = (
            "friendships/{user_id}/following/?max_id={max_id}"
            "&ig_sig_key_version={sig_key}&rank_token={rank_token}"
        ).format(
            user_id=user_id,
            max_id=max_id,
            sig_key=config.SIG_KEY_VERSION,
            rank_token=self.rank_token,
        )
        return self.send_request(url)

    def get_self_users_following(self):
        return self.get_user_followings(self.user_id)

    def get_user_followers(self, user_id, max_id=""):
        url = "friendships/{user_id}/followers/?rank_token={rank_token}"
        url = url.format(user_id=user_id, rank_token=self.rank_token)
        if max_id:
            url += "&max_id={max_id}".format(max_id=max_id)
        return self.send_request(url)

    def get_self_user_followers(self):
        return self.followers

    def follow(self, user_id):
        data = self.json_data(
            {
                "_csrftoken": self.token,
                "user_id": user_id,
                "radio_type": "wifi-none",
                "_uid": user_id,
                "device_id": self.device_id,
                "_uuid": self.uuid,
            }
        )
        # self.logger.debug("post data: {}".format(data))
        url = "friendships/create/{user_id}/".format(user_id=user_id)
        return self.send_request(url, data)

    def unfollow(self, user_id):
        data = self.json_data(
            {
                "surface": "profile",
                "_csrftoken": self.token,
                "user_id": user_id,
                "radio_type": "wifi-none",
                "_uid": user_id,
                "_uuid": self.uuid,
            }
        )
        url = "friendships/destroy/{user_id}/".format(user_id=user_id)
        return self.send_request(url, data)

    def remove_follower(self, user_id):
        data = self.json_data({"user_id": user_id})
        url = "friendships/remove_follower/{user_id}/".format(user_id=user_id)
        return self.send_request(url, data)

    def block(self, user_id):
        data = self.json_data({"user_id": user_id})
        url = "friendships/block/{user_id}/".format(user_id=user_id)
        return self.send_request(url, data)

    def unblock(self, user_id):
        data = self.json_data({"user_id": user_id})
        url = "friendships/unblock/{user_id}/".format(user_id=user_id)
        return self.send_request(url, data)

    def user_friendship(self, user_id):
        data = self.json_data({"user_id": user_id})
        url = "friendships/show/{user_id}/".format(user_id=user_id)
        return self.send_request(url, data)

    def all_friendship(self, user_id):
        url = "friendships/show_many"
        return self.send_request(url)

    def mute_user(self, user, mute_story=False, mute_posts=False):
        data_dict = {}
        if mute_posts:
            data_dict["target_posts_author_id"] = user
        if mute_story:
            data_dict["target_reel_author_id"] = user
        data = self.json_data(data_dict)
        url = "friendships/mute_posts_or_story_from_follow/"
        return self.send_request(url, data)

    def get_muted_friends(self, muted_content):
        # ToDo update endpoints for posts
        if muted_content == "stories":
            url = "friendships/muted_reels"
        elif muted_content == "posts":
            raise NotImplementedError(
                "API does not support getting friends "
                "with muted {}".format(muted_content)
            )
        else:
            raise NotImplementedError(
                "API does not support getting friends"
                " with muted {}".format(muted_content)
            )

        return self.send_request(url)

    def unmute_user(self, user, unmute_posts=False, unmute_stories=False):
        data_dict = {}
        if unmute_posts:
            data_dict["target_posts_author_id"] = user
        if unmute_stories:
            data_dict["target_reel_author_id"] = user
        data = self.json_data(data_dict)
        url = "friendships/unmute_posts_or_story_from_follow/"
        return self.send_request(url, data)

    def get_pending_friendships(self):
        """Get pending follow requests"""
        url = "friendships/pending/"
        return self.send_request(url, None, True, True, None, None, None)

    def approve_pending_friendship(self, user_id, main_list, index):
        data = self.json_data(
            {
                "_uuid": self.uuid,
                "_uid": self.user_id,
                "user_id": user_id,
                "_csrftoken": self.token,
            }
        )
        url = "friendships/approve/{}/".format(user_id)
        resp = self.send_request(url, post=data)
        main_list[index] = resp


    def reject_pending_friendship(self, user_id):
        data = self.json_data(
            {
                "_uuid": self.uuid,
                "_uid": self.user_id,
                "user_id": user_id,
                "_csrftoken": self.token,
            }
        )
        url = "friendships/ignore/{}/".format(user_id)
        return self.send_request(url, post=data)

    def get_direct_share(self):
        return self.send_request("direct_share/inbox/?")

    @staticmethod
    def _prepare_recipients(users, thread_id=None, use_quotes=False):
        if not isinstance(users, list):
            print("Users must be an list")
            return False
        result = {"users": "[[{}]]".format(",".join(users))}
        if thread_id:
            template = '["{}"]' if use_quotes else "[{}]"
            result["thread"] = template.format(thread_id)
        return result

    @staticmethod
    def generate_signature(data):
        body = (
                hmac.new(
                    config.IG_SIG_KEY.encode("utf-8"), data.encode("utf-8"), hashlib.sha256
                ).hexdigest()
                + "."
                + urllib.parse.quote(data)
        )
        signature = "signed_body={body}&ig_sig_key_version={sig_key}"
        return signature.format(sig_key=config.SIG_KEY_VERSION, body=body)

    @staticmethod
    def generate_device_id(seed):
        volatile_seed = "12345"
        m = hashlib.md5()
        m.update(seed.encode("utf-8") + volatile_seed.encode("utf-8"))
        return "android-" + m.hexdigest()[:16]

    @staticmethod
    def get_seed(*args):
        m = hashlib.md5()
        m.update(b"".join([arg.encode("utf-8") for arg in args]))
        return m.hexdigest()

    @staticmethod
    def generate_UUID(uuid_type):
        generated_uuid = str(uuid.uuid4())
        if uuid_type:
            return generated_uuid
        else:
            return generated_uuid.replace("-", "")



    def search_username(self, username):
        url = "users/{username}/usernameinfo/".format(username=username)
        return self.send_request(url)

    def search_tags(self, query):
        url = "tags/search/?is_typeahead=true&q={query}" "&rank_token={rank_token}"
        return self.send_request(url.format(query=query, rank_token=self.rank_token))

    def search_location(self, query="", lat=None, lng=None):
        url = (
            "fbsearch/places/?rank_token={rank_token}"
            "&query={query}&lat={lat}&lng={lng}"
        )
        url = url.format(rank_token=self.rank_token, query=query, lat=lat, lng=lng)
        return self.send_request(url)

    def get_user_reel(self, user_id):
        url = "feed/user/{}/reel_media/".format(user_id)
        return self.send_request(url)

    def get_reels_tray_feed(
            self, reason=None
    ):  # reason can be = cold_start or pull_to_refresh
        data = {
            "supported_capabilities_new": config.SUPPORTED_CAPABILITIES,
            "reason": reason,
            "_csrftoken": self.token,
            "_uuid": self.uuid,
        }
        data = json.dumps(data)
        return self.send_request("feed/reels_tray/", data)

    def get_reels_media(self):
        data = {
            "supported_capabilities_new": config.SUPPORTED_CAPABILITIES,
            "source": "feed_timeline",
            "_csrftoken": self.token,
            "_uuid": self.uuid,
            "_uid": self.user_id,
            "user_ids": self.user_id,
        }
        data = json.dumps(data)
        return self.send_request("feed/reels_media/", data)

    def push_register(self):
        data = {
            "device_type": "android_mqtt",
            "is_main_push_channel": "true",
            "device_sub_type": "2",
            # TODO find out what &device_token={"k":"eyJwbiI6ImNvbS5pbnN0YWdyYW0uYW5kcm9pZCIsImRpIjoiNzhlNGMxNmQtN2YzNC00NDlkLTg4OWMtMTAwZDg5OTU0NDJhIiwiYWkiOjU2NzMxMDIwMzQxNTA1MiwiY2siOiIxNjgzNTY3Mzg0NjQyOTQifQ==","v":0,"t":"fbns-b64"} is
            "device_token": "{'k':'eyJwbiI6ImNvbS5pbnN0YWdyYW0uYW5kcm9pZCIsImRpIjoiYmY5ZjNhOTUtMzdjMi00NjEwLTk2MDctYjk2YjI4MDc5YWU4IiwiYWkiOjU2NzMxMDIwMzQxNTA1MiwiY2siOiI5NTk0MzgzMTAyMTUzMzAifQ==','v':'0','t':'fbns-b64'}",
            "_csrftoken": self.token,
            "guid": self.uuid,
            "_uuid": self.uuid,
            "users": self.user_id,
            "familiy_device_id": "7e5a10af-3890-4892-ad0a-4656cd301a2b",
        }
        data = json.dumps(data)
        return self.send_request("push/register/", data)

    def media_blocked(self):
        url = "media/blocked/"
        return self.send_request(url)

    def get_users_reel(self, user_ids):
        """
            Input: user_ids - a list of user_id
            Output: dictionary: user_id - stories data.
            Basically, for each user output the same as after
            self.get_user_reel
        """
        url = "feed/reels_media/"
        res = self.send_request(
            url, post=self.json_data({"user_ids": [str(x) for x in user_ids]})
        )
        if res:
            return self.last_json["reels"] if "reels" in self.last_json else []
        return []

    def see_reels(self, reels):
        """
            Input - the list of reels jsons
            They can be aquired by using get_users_reel()
            or get_user_reel() methods
        """
        if not isinstance(reels, list):
            # In case of only one reel as input
            reels = [reels]

        story_seen = {}
        now = int(time.time())
        for i, story in enumerate(
                sorted(reels, key=lambda m: m["taken_at"], reverse=True)
        ):
            story_seen_at = now - min(
                i + 1 + random.randint(0, 2), max(0, now - story["taken_at"])
            )
            story_seen["{!s}_{!s}".format(story["id"], story["user"]["pk"])] = [
                "{!s}_{!s}".format(story["taken_at"], story_seen_at)
            ]

        data = self.json_data(
            {
                "reels": story_seen,
                "_csrftoken": self.token,
                "_uuid": self.uuid,
                "_uid": self.user_id,
            }
        )
        data = self.generate_signature(data)
        return self.session.post(
            "https://i.instagram.com/api/v2/" + "media/seen/", data=data
        ).ok

    def get_user_stories(self, user_id):
        url = "feed/user/{}/story/".format(user_id)
        return self.send_request(url)

    def get_self_story_viewers(self, story_id):
        url = ("media/{}/list_reel_media_viewer/?supported_capabilities_new={}").format(
            story_id, config.SUPPORTED_CAPABILITIES
        )
        return self.send_request(url)

    def get_tv_suggestions(self):
        url = "igtv/tv_guide/"
        return self.send_request(url)

    def get_hashtag_stories(self, hashtag):
        url = "tags/{}/story/".format(hashtag)
        return self.send_request(url)

    def follow_hashtag(self, hashtag):
        data = self.json_data({})
        url = "tags/follow/{}/".format(hashtag)
        return self.send_request(url, data)

    def unfollow_hashtag(self, hashtag):
        data = self.json_data({})
        url = "tags/unfollow/{}/".format(hashtag)
        return self.send_request(url, data)

    def get_tags_followed_by_user(self, user_id):
        url = "users/{}/following_tags_info/".format(user_id)
        return self.send_request(url)

    def get_hashtag_sections(self, hashtag):
        data = self.json_data(
            {
                "supported_tabs": "['top','recent','places']",
                "include_persistent": "true",
            }
        )
        url = "tags/{}/sections/".format(hashtag)
        return self.send_request(url, data)

    def get_media_insight(self, media_id):
        url = ("insights/media_organic_insights/{}/?ig_sig_key_version={}").format(
            media_id, config.IG_SIG_KEY
        )
        return self.send_request(url)

    def get_self_insight(self):
        # TODO:
        url = (
            "insights/account_organic_insights/?"
            "show_promotions_in_landing_page=true&first={}"
        ).format()
        return self.send_request(url)

    # From profile => "module_name":"feed_contextual_profile"
    # From home/feed => "module_name":"feed_timeline"
    def save_media(self, media_id, module_name="feed_timeline"):
        return self.send_request(
            endpoint="media/{media_id}/save/".format(media_id=media_id),
            post=self.json_data(self.action_data({"module_name": module_name})),
        )

    def unsave_media(self, media_id):
        data = self.json_data()
        url = "media/{}/unsave/".format(media_id)
        return self.send_request(url, data)

    def get_saved_medias(self):
        url = "feed/saved/"
        return self.send_request(url)

    def get_loom_fetch_config(self):
        return self.send_request("loom/fetch_config/")

    def get_request_country(self):
        return self.send_request("locations/request_country/")

    def get_linked_accounts(self):
        return self.send_request("linked_accounts/get_linkage_status/")

    def get_profile_notice(self):
        return self.send_request("users/profile_notice/")

    def get_business_branded_content(self):
        return self.send_request(
            "business/branded_content/should_require_professional_account/"
        )

    def get_monetization_products_eligibility_data(self):
        return self.send_request(
            "business/eligibility/get_monetization_products_eligibility_data/?product_types=branded_content"
        )

    def get_cooldowns(self):
        body = self.generate_signature(config.SIG_KEY_VERSION)
        url = ("qp/get_cooldowns/?{}").format(body)
        return self.send_request(url)

    def log_resurrect_attribution(self):
        data = {
            "_csrftoken": self.token,
            "_uuid": self.uuid,
            "_uid": self.user_id,
        }
        data = json.dumps(data)
        return self.send_request("attribution/log_resurrect_attribution/", data)

    def store_client_push_permissions(self):
        data = {
            "enabled": "true",
            "_csrftoken": self.token,
            "device_id": self.device_id,
            "_uuid": self.uuid,
        }
        data = json.dumps(data)
        return self.send_request("attribution/store_client_push_permissions/", data)

    def process_contact_point_signals(self):
        data = {
            "phone_id": self.phone_id,
            "_csrftoken": self.token,
            "_uid": self.user_id,
            "device_id": self.device_id,
            "_uuid": self.uuid,
            "google_tokens": "[]",
        }
        data = json.dumps(data)
        return self.send_request("accounts/process_contact_point_signals/", data)

    def write_supported_capabilities(self):
        data = {
            "supported_capabilities_new": config.SUPPORTED_CAPABILITIES,
            "_csrftoken": self.token,
            "_uid": self.user_id,
            "_uuid": self.uuid,
        }
        data = json.dumps(data)
        return self.send_request("creatives/write_supported_capabilities/", data)

    def arlink_download_info(self):
        return self.send_request("users/arlink_download_info/?version_override=2.2.1")

    def get_direct_v2_inbox(self):
        return self.send_request(
            "direct_v2/inbox/?visual_message_return_type=unseen&thread_message_limit=10&persistentBadging=true&limit=20"
        )

    def get_direct_v2_inbox2(self):
        return self.send_request(
            "direct_v2/inbox/?visual_message_return_type=unseen&persistentBadging=true&limit=0"
        )

    def topical_explore(self):
        url = (
            "discover/topical_explore/?is_prefetch=true&omit_cover_media=true&use_sectional_payload=true&timezone_offset=0&session_id={}&include_fixed_destinations=true"
        ).format(self.client_session_id)
        return self.send_request(url)

    def notification_badge(self):
        data = {
            "phone_id": self.phone_id,
            "_csrftoken": self.token,
            "user_ids": self.user_id,
            "device_id": self.device_id,
            "_uuid": self.uuid,
        }
        data = json.dumps(data)
        return self.send_request("notifications/badge/", data)

    def facebook_ota(self):
        url = (
                "facebook_ota/?fields=update{download_uri,download_uri_delta_base,version_code_delta_base,download_uri_delta,fallback_to_full_update,file_size_delta,version_code,published_date,file_size,ota_bundle_type,resources_checksum,allowed_networks,release_id}&custom_user_id=3149016955&"
                + self.generate_signature(config.SIG_KEY_VERSION)
                + "&version_code=200396023&version_name="
                + config.APP_VERSION
                + "&custom_app_id=124024574287414&custom_device_id="
                + self.phone_id
                + ""
        )
        return self.send_request(url)

    # ====== DIRECT METHODS ====== #
    def get_inbox_v2(self):
        data = json.dumps(
            {
                "visual_message_return_type": "unseen",
                "persistentBadging": "True",
                "limit": "0",
            }
        )
        return self.send_request("direct_v2/inbox/", data)

    def get_presence(self):
        return self.send_request("direct_v2/get_presence/")

    def get_thread(self, thread_id, cursor_id=None):
        data = json.dumps(
            {"visual_message_return_type": "unseen", "seq_id": "40065", "limit": "10"}
        )
        if cursor_id is not None:
            data["cursor"] = cursor_id
        return self.send_request(
            "direct_v2/threads/{}/".format(thread_id), json.dumps(data)
        )

    def get_ranked_recipients(self, mode, show_threads, query=None):
        data = {
            "mode": mode,
            "show_threads": "false" if show_threads is False else "true",
            "use_unified_inbox": "true",
        }
        if query is not None:
            data["query"] = query
        return self.send_request("direct_v2/ranked_recipients/", json.dumps(data))

    def get_scores_bootstrap(self):
        url = "scores/bootstrap/users/?surfaces={surfaces}"
        url = url.format(
            surfaces='["autocomplete_user_list","coefficient_besties_list_ranking","coefficient_rank_recipient_user_suggestion","coefficient_ios_section_test_bootstrap_ranking","coefficient_direct_recipients_ranking_variant_2"]'
        )
        return self.send_request(url)



    def get_pending_inbox(self):
        url = (
            "direct_v2/pending_inbox/?persistentBadging=true" "&use_unified_inbox=true"
        )
        return self.send_request(url)

    # ACCEPT button in pending request
    def approve_pending_thread(self, thread_id):
        data = self.json_data({"_uuid": self.uuid, "_csrftoken": self.token})
        url = "direct_v2/threads/{}/approve/".format(thread_id)
        return self.send_request(url, post=data)

    # DELETE button in pending request
    def hide_pending_thread(self, thread_id):
        data = self.json_data({"_uuid": self.uuid, "_csrftoken": self.token})
        url = "direct_v2/threads/{}/hide/".format(thread_id)
        return self.send_request(url, post=data)

    # BLOCK button in pending request
    def decline_pending_thread(self, thread_id):
        data = self.json_data({"_uuid": self.uuid, "_csrftoken": self.token})
        url = "direct_v2/threads/{}/decline/".format(thread_id)
        return self.send_request(url, post=data)

    def open_instagram_link(self, link):
        return self.send_request(
            "oembed/?url={}".format(urllib.parse.quote(link, safe=""))
        )