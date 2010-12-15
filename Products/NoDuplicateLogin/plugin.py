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

"""NoDuplicatePlugin
"""

__author__ = "Daniel Nouri <daniel.nouri@gmail.com>"

from urllib import quote, unquote

from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.Cache import Cacheable


from Products.PluggableAuthService.plugins.BasePlugin import BasePlugin
from Products.PluggableAuthService.utils import classImplements
from Products.PluggableAuthService.interfaces.plugins \
     import IAuthenticationPlugin, ICredentialsResetPlugin

from utils import uuid

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
manage_addNoDuplicateLoginForm = PageTemplateFile(
    'www/noduplicateloginAdd',
    globals(),
    __name__='manage_addNoDuplicateLoginForm' )

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

    meta_type = 'No Duplicate Plugin'
    cookie_name = '__noduplicate'
    security = ClassSecurityInfo()

    _properties = ( { 'id'    : 'title'
                    , 'label' : 'Title'
                    , 'type'  : 'string'
                    , 'mode'  : 'w'
                    }
                  , { 'id'    : 'cookie_name'
                    , 'label' : 'Cookie Name'
                    , 'type'  : 'string'
                    , 'mode'  : 'w'
                    }
                  )

    # UIDs older than three days are deleted from our storage...
    time_to_delete_cookies = 3
    # ... every 1000th request
    cookie_cleanup_period = 1000

    _dont_swallow_my_exceptions = True

    def __init__(self, id, title=None, cookie_name=''):
        self._id = self.id = id
        self.title = title

        if cookie_name:
            self.cookie_name = cookie_name


    security.declarePrivate('authenticateCredentials')
    def authenticateCredentials(self, credentials):
        """See IAuthenticationPlugin.

        This plugin will actually never authenticate.

        o We expect the credentials to be those returned by
          ILoginPasswordExtractionPlugin.
        """



        request = self.REQUEST
        response = request['RESPONSE']
        session = request.SESSION
        pas_instance = self._getPAS()

        login = credentials.get('cookie')

        if None in (login, pas_instance):
            return None

        cookie_val = self.getCookie()

        if cookie_val and 'mapping1' in session.keys():
            # A cookie value is there.  If it's the same as the value
            # in our mapping, it's fine.  Otherwise we'll force a
            # logout.
            existing_uid = session['mapping1'].get(login)
            if existing_uid and cookie_val != existing_uid[0]:
                # The cookies values differ, we want to logout the
                # user by calling resetCredentials.  Note that this
                # will eventually call our own resetCredentials which
                # will cleanup our own cookie.
                self.resetAllCredentials(request, response)
                request['portal_status_message'] = (
                    "Someone else logged in under your name.  You have been "
                    "logged out.")
            elif existing_uid is None:
                # The browser has the cookie but we don't know about
                # it.  Let's reset our own cookie:
                self.setCookie('')
        
        else:
            # When no cookie is present, we generate one, store it and
            # set it in the response:
            cookie_val = uuid()

            # do some cleanup in our mappings
            #existing_uid = session['mapping1'].get(login)
            #if existing_uid:
            #    if session['mapping2'].has_key(existing_uid[0]):
            #        del session['mapping2'][existing_uid[0]]

            now = DateTime()
            session['mapping1'] = {'login': (cookie_val, now)}
            session['mapping2'] = {'cookie_val': (login, now)}
            self.setCookie(cookie_val)
            
        return None # Note that we never return anything useful


    security.declarePrivate('resetCredentials')
    def resetCredentials(self, request, response):
        """See ICredentialsResetPlugin.
        """
        cookie_val = self.getCookie()
        session = self.REQUEST.SESSION
        if cookie_val:
            loginanddate = session['mapping2'].get(cookie_val)
            if loginanddate:
                login, date = loginanddate
                del session['mapping2'][cookie_val]
                existing_uid = self['mapping1'].get(login)
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
        """Helper to retrieve the cookie value 
        """
        request = self.REQUEST
        response = request['RESPONSE']
        cookie = request.SESSION.get(self.cookie_name, '')
        return unquote(cookie)

    security.declarePrivate('setCookie')
    def setCookie(self, value):
        """Helper to set the cookie value 

        o Setting to '' means delete.
        """
        value = quote(value)
        request = self.REQUEST
        response = request['RESPONSE']

        request.SESSION.set(self.cookie_name, value)


classImplements(NoDuplicateLogin,
                IAuthenticationPlugin,
                ICredentialsResetPlugin)

InitializeClass(NoDuplicateLogin)
