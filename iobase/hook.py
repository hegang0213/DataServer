import uuid
import time


class Hook(object):

    def __init__(self):
        self._hooks = {}

    def add_hook(self, any_object):
        uid = str(uuid.uuid1())
        self._hooks[uid] = any_object
        return uid

    def set_hook(self, uid, any_object):
        self._hooks[uid] = any_object

    def remove_hook(self, uid):
        if self._hooks.get(uid) is not None:
            self._hooks.pop(uid)

    def get_hook(self, uid):
        return self._hooks.get(uid)

    def get_hooks(self):
        return self._hooks

    def remove_timeout(self):
        now = int(time.time())
        keys = list(self._hooks.keys())
        for key in keys:
            ho = self._hooks.get(key)
            if now - ho.timestamp > 180:
                del self._hooks[key]


class HookObject:
    def __init__(self, t, values):
        self.timestamp = int(t)
        self.values = values
