# Copyright (c) 2006, BlueDynamics, Klein & Partner KEG, Innsbruck,
# Austria, and the respective authors. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""NoDuplicateLogin plugin
"""

__author__ = "Daniel Nouri <daniel.nouri@gmail.com>"

from AccessControl import ClassSecurityInfo, Permissions
#from BTrees.LLBTree import LLBTree
#from BTrees.LOBTree import LOBTree
from BTrees.OOBTree import OOBTree
from BTrees.OLBTree import OLBTree
import time
import uuid
from Globals import InitializeClass
from OFS.Cache import Cacheable
from Products.CMFPlone import PloneMessageFactory as _
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.plugins \
     import IAuthenticationPlugin, ICredentialsResetPlugin, ICredentialsUpdatePlugin


try:
    from Products.statusmessages.interfaces import IStatusMessage
except:
    IStatusMessage = NotImplemented

from urllib import quote, unquote


DAYS = 60 * 60 * 24

manage_addNoDuplicateLoginForm = PageTemplateFile(
    'www/noduplicateloginAdd',
    globals(),
    __name__='manage_addNoDuplicateLoginForm')


def manage_addNoDuplicateLogin(dispatcher,
                               id,
                               title=None,
                               cookie_name='',
                               REQUEST=None):
    """Add a NoDuplicateLogin plugin to a Pluggable Auth Service."""

    obj = NoDuplicateLogin(id, title,
                           cookie_name=cookie_name)
    dispatcher._setObject(obj.getId(), obj)

    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect('%s/manage_workspace?manage_tabs_message='
                                     'NoDuplicateLogin+plugin+added.'
                                     % dispatcher.absolute_url())


class NoDuplicateLogin(BasePlugin, Cacheable):

    """PAS plugin that rejects multiple logins with the same user at
    the same time, by forcing a logout of all but one user.
    """

    meta_type = 'No Duplicate Login Plugin'
    cookie_name = '__noduplicate'
    security = ClassSecurityInfo()

    _properties = (
        {'id': 'title', 'label': 'Title', 'type': 'string', 'mode': 'w'},
        {'id': 'cookie_name', 'label': 'Cookie Name', 'type': 'string',
            'mode': 'w'},
        )

    # UIDs older than three days are deleted from our storage...
    time_to_delete_cookies = 3 * DAYS

    def __init__(self, id, title=None, cookie_name=''):
        self._id = self.id = id
        self.title = title

        if cookie_name:
            self.cookie_name = cookie_name

        self._userid_to_uuid = OOBTree()  # userid : uuid.uuid4().hex
        self._uuid_to_time = OLBTree()    # uuid : int(time.time())
        self._uuid_to_userid = OOBTree()  # uuid.uuid4().hex : userid

    security.declarePrivate('authenticateCredentials')

    def authenticateCredentials(self, credentials):
        """See IAuthenticationPlugin.

        This plugin will actually never authenticate.

        o We expect the credentials to be those returned by
          ILoginPasswordExtractionPlugin.
        """
        request = self.REQUEST
        response = request['RESPONSE']

        login = credentials.get('login')
        if login is None:
            # We check with the downstream authenticators to see if they can fill it in for us
            plugins = self._getPAS().plugins
            authenticators = plugins.listPlugins( IAuthenticationPlugin )
            for authenticator_id, auth in authenticators:
                if authenticator_id == self.id:
                    # Avoid recursion
                    continue
                try:
                    uid_and_info = auth.authenticateCredentials( credentials )
                    if uid_and_info is None:
                        continue
                    user_id, info = uid_and_info
                except StandardError:
                    # We squelch all errors here, they'll be re-raised by the plugin itself
                    # if appropriate
                    continue
                login = user_id

        cookie_val = self.getCookie()
        
        if cookie_val:
            # A cookie value is there.  If it's the same as the value
            # in our mapping, it's fine.  Otherwise we'll force a
            # logout.
            existing_uid = self._userid_to_uuid.get(login)
            if existing_uid and (cookie_val != existing_uid):
                # The cookies values differ, we want to logout the
                # user by calling resetCredentials.  Note that this
                # will eventually call our own resetCredentials which
                # will cleanup our own cookie.
                self.resetAllCredentials(request, response)
                if existing_uid == 'FORCED_LOGOUT':
                    message = _(u"An administrator has ended your session.")
                else:
                    message = _(
                            u"Someone else logged in under your name. You have been "
                            "logged out")
                if IStatusMessage is not NotImplemented:
                    try:
                        IStatusMessage(request).add(message, "error")
                    except TypeError:
                        # Status messages aren't possible for this request
                        pass
                # If a credential isn't resettable we can fake it by clearing
                # the (mutable) credentials dictionary we recieved, so downstream
                # plugins won't succeed. This won't be persistent, but it could cause challenges
                # to be re-issued.
                credentials.clear()
            elif existing_uid is None:
                # The browser has the cookie but we don't know about
                # it.  Let's reset our own cookie:
                self.setCookie('')

        else:
            # When no cookie is present, we generate one, store it and
            # set it in the response
            self.updateCredentials(self.REQUEST, self.REQUEST.RESPONSE, login, credentials.get("password"))
            
        return None  # Note that we never return anything useful

    security.declarePrivate('logUserOut')
    def logUserOut(self, login):
        """ Change the unique authorisation code for a user, causing them to become logged out """
        
        uuid = self._userid_to_uuid.get(login)
        date = self._uuid_to_time.get(uuid)
        
        self._userid_to_uuid[login] = 'FORCED_LOGOUT'
        
        if date is not None:
            del self._uuid_to_time[uuid]
        if uuid is not None:
            del self._uuid_to_userid[uuid]
        
    
    security.declarePrivate('resetCredentials')

    def resetCredentials(self, request, response):
        """See ICredentialsResetPlugin.
        """
        cookie_val = self.getCookie()
        if cookie_val:
            login = self._uuid_to_userid.get(cookie_val)
            date = self._uuid_to_time.get(cookie_val)
            if login is not None:
                del self._userid_to_uuid[login]
            if date is not None:
                del self._uuid_to_time[cookie_val]
            try:
                del self._uuid_to_userid[cookie_val]
            except KeyError:
                # The record's already been removed for us
                pass

        self.setCookie('')

    security.declarePrivate('resetAllCredentials')

    def resetAllCredentials(self, request, response):
        """Call resetCredentials of all plugins.

        o This is not part of any contract.
        """
        # This is arguably a bit hacky, but calling
        # pas_instance.resetCredentials() will not do anything because
        # the user is still anonymous.  (I think it should do
        # something nevertheless.)
        pas_instance = self._getPAS()
        plugins = pas_instance._getOb('plugins')
        cred_resetters = plugins.listPlugins(ICredentialsResetPlugin)
        for resetter_id, resetter in cred_resetters:
            resetter.resetCredentials(request, response)

    # ICredentialsUpdatePlugin implementation
    def updateCredentials(self, request, response, login, new_password):
        """
        When updateCredentials is called we can take this opportunity to generate a new
        UUID and store it unconditionally. This has the advantage of solving conflict errors when
        serving resources after the first page load.
        """
        # Check that this user is our responsibility
        pas = self._getPAS()
        info = pas._verifyUser(pas.plugins, login=login)
        if info is not None:
            # Generate a uuid to represent the users
            cookie_val = uuid.uuid4().hex
            # do some cleanup in our mappings, remove their old session backreferences
            existing_uid = self._userid_to_uuid.get(login)
            if existing_uid:
                if existing_uid in self._uuid_to_userid:
                    del self._uuid_to_userid[existing_uid]
                if existing_uid in self._uuid_to_time:
                    del self._uuid_to_time[existing_uid]
            
            # Get the current time as seconds since 1970, as it's int-ey and likes BTrees
            now = int(time.time())
            self._userid_to_uuid[login] = cookie_val
            self._uuid_to_time[cookie_val] = now
            self._uuid_to_userid[cookie_val] = login
            # Set the new cookie into the response
            self.setCookie(cookie_val, response=response)
        

    security.declarePrivate('getCookie')
    def getCookie(self):
        """Helper to retrieve the cookie value from either cookie or
        session, depending on policy.
        """
        request = self.REQUEST
        cookie = request.get(self.cookie_name, '')
        return unquote(cookie)

    security.declarePrivate('setCookie')

    def setCookie(self, value, response=None):
        """Helper to set the cookie value to either cookie or
        session, depending on policy.

        o Setting to '' means delete.
        """
        value = quote(value)
        if response is None:
            request = self.REQUEST
            response = request['RESPONSE']

        if value:
            response.setCookie(self.cookie_name, value, path='/')
        else:
            response.expireCookie(self.cookie_name, path='/')

    security.declareProtected(Permissions.manage_users, 'cleanUp')

    def cleanUp(self):
        """Clean up storage.

        Call this periodically through the web to clean up old entries
        in the storage."""
        count = 0
        
        expiry = int(time.time()) - self.time_to_delete_cookies

        for u, t in self._uuid_to_time.items():
            if t < expiry:
                login = self._uuid_to_userid.get(u)
                del self._uuid_to_time[u]
                del self._uuid_to_userid[u]
                if login:
                    del self._userid_to_uuid[login]
                
        return "%s entries deleted." % count

classImplements(NoDuplicateLogin,
                IAuthenticationPlugin,
                ICredentialsResetPlugin,
                ICredentialsUpdatePlugin)

InitializeClass(NoDuplicateLogin)
