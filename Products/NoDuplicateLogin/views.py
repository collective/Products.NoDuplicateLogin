import datetime

from Products.Five.browser import BrowserView

class RevokeSession(BrowserView):
    
    def has_nodupe(self):
        return bool(self.context.acl_users.objectValues('No Duplicate Login Plugin'))
    
    def sessions(self):
        nodupe = self.context.acl_users.objectValues('No Duplicate Login Plugin')[0]
        for login, uuid in nodupe._userid_to_uuid.items():
            if uuid == 'FORCED_LOGOUT':
                continue
            time = nodupe._uuid_to_time.get(uuid, 0)
            yield {"username": login, "time": datetime.datetime.fromtimestamp(time)}
    
    def do_remove(self):
        nodupe = self.context.acl_users.objectValues('No Duplicate Login Plugin')[0]
        nodupe.logUserOut(self.request['user'])
        return self.request.RESPONSE.redirect(self.context.absolute_url()+"/revoke_session")
