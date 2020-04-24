import json
import time
from . import config, devices


def sync_device_features(self, login=None):
    data = {
        "id": self.uuid,
        "server_config_retrieval": "1",
        "experiments": config.LOGIN_EXPERIMENTS,
    }
    if login is False:
        data["id"] = self.user_id
        data["_uuid"] = self.uuid
        data["_uid"] = self.user_id
        data["_csrftoken"] = self.token
    data = json.dumps(data)
    self.last_experiments = time.time()
    return self.send_request(
        "qe/sync/", data, login=login, headers={"X-DEVICE-ID": self.uuid}
    )


def sync_launcher(self, login=None):
#######################################################
    import sys
    sys.path.append("../../")
    from flask import session
    from project.users.memcache_ctrl import client
    client.get(session["username"]["username"])
########################################################

    data = {
        "id": self.uuid,
        "server_config_retrieval": "1",
    }
    if login is False:
        data["_uid"] = self.user_id
        data["_uuid"] = self.uuid
        data["_csrftoken"] = self.token
    data = json.dumps(data)
    return self.send_request("launcher/sync/", data, login=login)


def set_contact_point_prefill(self, usage=None, login=False):
    data = {
        "phone_id": self.phone_id,
        "usage": usage,
    }
    if login is False:
        data["_csrftoken"] = self.token
    data = json.dumps(data)
    return self.send_request("accounts/contact_point_prefill/", data, login=True)


def get_prefill_candidates(self, login=False):
    data = {
        "android_device_id": self.device_id,
        "phone_id": self.phone_id,
        "usages": '["account_recovery_omnibox"]',
        "device_id": self.uuid,
    }
    if login is False:
        data["_csrftoken"] = self.token
        data["client_contact_points"] = (
            '["type":"omnistring","value":"{}","source":"last_login_attempt"]'.format(
                self.username
            ),
        )
    data = json.dumps(data)
    return self.send_request("accounts/get_prefill_candidates/", data, login=login)


def get_account_family(self):
    return self.send_request("multiple_accounts/get_account_family/")


def get_zr_token_result(self):
    url = (
        "zr/token/result/?device_id={rank_token}"
        "&token_hash=&custom_device_id={custom_device_id}&fetch_reason=token_expired"
    )
    url = url.format(rank_token=self.device_id, custom_device_id=self.uuid)
    return self.send_request(url)


def banyan(self):
    url = 'banyan/banyan/?views=["story_share_sheet","threads_people_picker","group_stories_share_sheet","reshare_share_sheet"]'
    return self.send_request(url)


def igtv_browse_feed(self):
    url = "igtv/browse_feed/?prefetch=1"
    return self.send_request(url)


def creatives_ar_class(self):
    data = {
        "_csrftoken": self.token,
        "_uuid": self.uuid,
    }
    data = json.dumps(data)
    return self.send_request("creatives/ar_class/", data)


def pre_login_flow(self):
    self.set_contact_point_prefill("prefill", True)
    self.sync_device_features(True)
    self.sync_launcher(True)
    self.get_prefill_candidates(True)


def login_flow(self, just_logged_in=False, app_refresh_interval=1800):
    self.last_experiments = time.time()
    check_flow = []
    try:
        check_flow.append(self.sync_launcher(False))
        check_flow.append(self.get_zr_token_result())
        check_flow.append(self.sync_device_features(False))
    except Exception as e:
        return False
    return False if False in check_flow else True


def set_device(self):
    self.device_settings = devices.DEVICES[self.device]
    self.user_agent = config.USER_AGENT_BASE.format(**self.device_settings)


def generate_all_uuids(self):
    self.phone_id = self.generate_UUID(uuid_type=True)
    self.uuid = self.generate_UUID(uuid_type=True)
    self.client_session_id = self.generate_UUID(uuid_type=True)
    self.advertising_id = self.generate_UUID(uuid_type=True)
    self.device_id = self.generate_device_id(
        self.get_seed(self.username, self.password)
    )


def reinstall_app_simulation(self):
    self.phone_id = self.generate_UUID(uuid_type=True)


def change_device_simulation(self):
    self.reinstall_app_simulation()
    self.device_id = self.generate_device_id(
        self.get_seed(self.generate_UUID(uuid_type=True)))