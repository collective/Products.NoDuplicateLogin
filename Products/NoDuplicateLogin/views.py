import datetime

from Products.Five.browser import BrowserView

class RevokeSession(BrowserView):
    
    def has_nodupe(self):
        return bool(self.context.acl_users.objectValues('No Duplicate Login Plugin'))
    
    def get_plugin(self):
        if not hasattr(self, 'plugin'):
            self.plugin = self.context.acl_users.objectValues('No Duplicate Login Plugin')[0]
        return self.plugin
    
    def visible_sessions(self):
        nodupe = self.get_plugin()
        return tuple(nodupe._userid_to_uuid.keys())
    
    def sessions(self):
        nodupe = self.get_plugin()
        for login in self.visible_sessions():
            uuid = nodupe._userid_to_uuid[login]
            if uuid == 'FORCED_LOGOUT':
                continue
            time = nodupe._uuid_to_time.get(uuid, 0)
            yield {"username": login, "time": datetime.datetime.fromtimestamp(time)}
    
    def do_remove(self):
        username = self.request['user']
        if username in self.visible_sessions():
            nodupe = self.get_plugin()
            nodupe.logUserOut(username)
        return self.request.RESPONSE.redirect(self.context.absolute_url()+"/revoke_session")
