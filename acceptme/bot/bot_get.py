def get_pending_follow_requests(self):
    import sys
    sys.path.append("../../")
    from flask import session
    from project.users.memcache_ctrl import client

    api = client.get(session["username"]["username"])["api"]
    api.get_pending_friendships()
    res = api.last_json.get("users")
    if res:
        return res
    return []

    # self.api.get_pending_friendships()
    # if self.api.last_json.get("users"):
    #     return self.api.last_json.get("users")
    # else:
    #     return []