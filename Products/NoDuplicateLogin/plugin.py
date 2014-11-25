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
from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from Globals import InitializeClass
from OFS.Cache import Cacheable
from Products.CMFPlone import PloneMessageFactory as _
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.plugins \
     import IAuthenticationPlugin, ICredentialsResetPlugin


try:
    from Products.statusmessages.interfaces import IStatusMessage
except:
    IStatusMessage = NotImplemented

from urllib import quote, unquote
from utils import uuid

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
    time_to_delete_cookies = 3

    # XXX I wish I had a better explanation for this, but disabling this makes
    # both the ZMI (basic auth) work and the NoDuplicateLogin work.
    # Otherwise, we get a traceback on basic auth. I suspect that means this
    # plugin needs to handle basic auth better but I'm not sure how or why.
    # Normally, we would prefer to see our exceptions.
    _dont_swallow_my_exceptions = False

    def __init__(self, id, title=None, cookie_name=''):
        self._id = self.id = id
        self.title = title

        if cookie_name:
            self.cookie_name = cookie_name

        self.mapping1 = OOBTree()  # userid : (UID, DateTime)
        self.mapping2 = OOBTree()  # UID : (userid, DateTime)

        self.plone_session = None  # for plone.session

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
                if auth is self:
                    # Avoid recursion
                    continue
                try:
                    uid_and_info = auth.authenticateCredentials(
                        credentials )
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
            existing_uid = self.mapping1.get(login)
            if existing_uid and cookie_val != existing_uid[0]:
                # The cookies values differ, we want to logout the
                # user by calling resetCredentials.  Note that this
                # will eventually call our own resetCredentials which
                # will cleanup our own cookie.
                self.resetAllCredentials(request, response)
                if IStatusMessage is not NotImplemented:
                    try:
                        IStatusMessage(request).add(_(
                            u"Someone else logged in under your name. You have been "
                            "logged out"), "error")
                    except TypeError:
                        # Status messages aren't possible for this request
                        pass
                # If a credential isn't resettable we can fake it by clearing
                # the (mutable) credentials dictionary we recieved, so downstream
                # plugins won't succeed
                credentials.clear()
            elif existing_uid is None:
                # The browser has the cookie but we don't know about
                # it.  Let's reset our own cookie:
                self.setCookie('')

        else:
            # When no cookie is present, we generate one, store it and
            # set it in the response:
            cookie_val = uuid()
            # do some cleanup in our mappings
            existing_uid = self.mapping1.get(login)
            if existing_uid:
                if existing_uid[0] in self.mapping2:
                    del self.mapping2[existing_uid[0]]

            now = DateTime()
            self.mapping1[login] = cookie_val, now
            self.mapping2[cookie_val] = login, now
            self.setCookie(cookie_val)

        return None  # Note that we never return anything useful

    security.declarePrivate('resetCredentials')

    def resetCredentials(self, request, response):
        """See ICredentialsResetPlugin.
        """
        cookie_val = self.getCookie()
        if cookie_val:
            loginanddate = self.mapping2.get(cookie_val)
            if loginanddate:
                login, date = loginanddate
                del self.mapping2[cookie_val]
                existing_uid = self.mapping1.get(login)
                if existing_uid:
                    assert existing_uid[0] != cookie_val

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

    security.declarePrivate('getCookie')

    def getCookie(self):
        """Helper to retrieve the cookie value from either cookie or
        session, depending on policy.
        """
        request = self.REQUEST
        cookie = request.get(self.cookie_name, '')
        return unquote(cookie)

    security.declarePrivate('setCookie')

    def setCookie(self, value):
        """Helper to set the cookie value to either cookie or
        session, depending on policy.

        o Setting to '' means delete.
        """
        value = quote(value)
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
        expiry = DateTime() - self.time_to_delete_cookies

        def cleanStorage(mapping):
            count = 0
            for key, (value, time) in mapping.items():
                if time < expiry:
                    del mapping[key]
                    count += 1
            return count

        for mapping in self.mapping1, self.mapping2:
            count = cleanStorage(mapping)

        return "%s entries deleted." % count

classImplements(NoDuplicateLogin,
                IAuthenticationPlugin,
                ICredentialsResetPlugin)

InitializeClass(NoDuplicateLogin)
