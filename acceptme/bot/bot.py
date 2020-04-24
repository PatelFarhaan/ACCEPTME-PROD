version = "1.0.0"
import datetime
import os
import random
import time

import sys
sys.path.append("../../")
from ..api import API
from .bot_follow import approve_pending_follow_requests
from .bot_get import get_pending_follow_requests
current_path = os.path.abspath(os.getcwd())


class Bot(object):
    def __init__(
        self,
        proxy=None,
        max_following_to_block=2000,
        verbosity=True,
        device=None,
    ):
        self.api = API(
            device=device,
        )
        # self.state = BotState()
        self.delays = {}
        self.max_per_day = {}
        self.max_following_to_block = max_following_to_block
        self.proxy = proxy
        self.verbosity = verbosity
        self.main_list = []

    @property
    def user_id(self):
        # For compatibility
        return self.api.user_id

    @property
    def username(self):
        # For compatibility
        return self.api.username

    @property
    def password(self):
        # For compatibility
        return self.api.password

    @property
    def last_json(self):
        # For compatibility
        return self.api.last_json

    @property
    def blacklist(self):
        # This is a fast operation because
        # `get_user_id_from_username` is cached.
        return [
            self.convert_to_user_id(i)
            for i in self.blacklist_file.list
            if i is not None
        ]

    @property
    def whitelist(self):
        # This is a fast operation because
        # `get_user_id_from_username` is cached.
        return [
            self.convert_to_user_id(i)
            for i in self.whitelist_file.list
            if i is not None
        ]

    @property
    def following(self):
        now = time.time()
        last = self.last.get("updated_following", now)
        if self._following is None or (now - last) > 7200:
            self.console_print("`bot.following` is empty, will download.", "green")
            self._following = self.get_user_following(self.user_id)
            self.last["updated_following"] = now
        return self._following

    @property
    def followers(self):
        now = time.time()
        last = self.last.get("updated_followers", now)
        if self._followers is None or (now - last) > 7200:
            self.console_print("`bot.followers` is empty, will download.", "green")
            self._followers = self.get_user_followers(self.user_id)
            self.last["updated_followers"] = now
        return self._followers

    @property
    def start_time(self):
        return self.state.start_time

    @start_time.setter
    def start_time(self, value):
        self.state.start_time = value

    @property
    def total(self):
        return self.state.total

    @total.setter
    def total(self, value):
        self.state.total = value

    @property
    def sleeping_actions(self):
        return self.state.sleeping_actions

    @sleeping_actions.setter
    def sleeping_actions(self, value):
        self.state.sleeping_actions = value

    @property
    def blocked_actions(self):
        return self.state.blocked_actions

    @blocked_actions.setter
    def blocked_actions(self, value):
        self.state.blocked_actions = value

    @property
    def last(self):
        return self.state.last

    @last.setter
    def last(self, value):
        self.state.last = value

    @property
    def _following(self):
        return self.cache.following

    @_following.setter
    def _following(self, value):
        self.cache.following = value

    @property
    def _followers(self):
        return self.cache.followers

    @_followers.setter
    def _followers(self, value):
        self.cache.followers = value

    @property
    def _user_infos(self):
        return self.cache.user_infos

    @_user_infos.setter
    def _user_infos(self, value):
        self.cache.user_infos = value

    @property
    def _usernames(self):
        return self.cache.usernames

    @_usernames.setter
    def _usernames(self, value):
        self.cache.usernames = value

    @staticmethod
    def version():
        try:
            from pip._vendor import pkg_resources
        except ImportError:
            import pkg_resources
        return next(
            (
                p.version
                for p in pkg_resources.working_set
                if p.project_name.lower() == "acceptme"
            ),
            "No match",
        )

    def logout(self, *args, **kwargs):
        self.api.logout()

    def login(self, **args):
        if self.proxy:
            args["proxy"] = self.proxy

        result = self.api.login(**args)

        import sys
        sys.path.append("../../")
        from flask import session
        from project.users.memcache_ctrl import client

        if session["username"]["singleton"]:
            cl_obj = {}
            cl_obj["api"] = self.api
            client.set(args["username"], cl_obj)
            session["username"]["singleton"] = False
            session.modified = True

        if result != True:
            return result
        return True


    ###############################


    def delay(self, key):
        last_action, target_delay = self.last[key], self.delays[key]
        elapsed_time = time.time() - last_action
        if elapsed_time < target_delay:
            t_remaining = target_delay - elapsed_time
            time.sleep(t_remaining * random.uniform(0.25, 1.25))
        self.last[key] = time.time()

    def error_delay(self):
        time.sleep(10)

    def small_delay(self):
        time.sleep(random.uniform(0.75, 3.75))

    def very_small_delay(self):
        time.sleep(random.uniform(0.175, 0.875))

    def reached_limit(self, key):
        current_date = datetime.datetime.now()
        passed_days = (current_date.date() - self.start_time.date()).days
        if passed_days > 0:
            self.reset_counters()
        return self.max_per_day[key] - self.total[key] <= 0

    def reset_counters(self):
        for k in self.total:
            self.total[k] = 0
        for k in self.blocked_actions:
            self.blocked_actions[k] = False
        self.start_time = datetime.datetime.now()

    def get_pending_follow_requests(self):
        return get_pending_follow_requests(self)

    def approve_pending_follow_requests(self, number_of_requests, ctr_item, init_dict_items, dict_get_index, counter_ctr):
        return approve_pending_follow_requests(self, number_of_requests, ctr_item, init_dict_items, dict_get_index, counter_ctr)