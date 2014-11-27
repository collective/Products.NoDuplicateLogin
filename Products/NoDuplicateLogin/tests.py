import re
import unittest

from plone.app.testing import FunctionalTesting as ploneFunctionalTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import setRoles
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID, TEST_USER_NAME, TEST_USER_PASSWORD
from plone.testing import Layer
from plone.testing import z2
from Products.PluggableAuthService.Extensions import upgrade
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin

            
WHOAMI_SCRIPT = """
##bind context=context
return context.REQUEST['AUTHENTICATED_USER']
"""


class NDLFixture(Layer):
    defaultBases = (z2.STARTUP,)
    
    def setUp(self):
        with z2.zopeApp() as app:
            z2.installProduct(app, 'Products.PluggableAuthService')
            z2.installProduct(app, 'Products.NoDuplicateLogin')
            z2.installProduct(app, 'Products.PythonScripts')
            
            app.manage_addProduct['PythonScripts'].manage_addPythonScript("whoami")
            whoami = app.whoami
            whoami.write(WHOAMI_SCRIPT)
        
NDL_FIXTURE = NDLFixture()

class NDLPlone(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, NDL_FIXTURE)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import Products.NoDuplicateLogin
        self.loadZCML(package=Products.NoDuplicateLogin)
    
    def setUpPloneSite(self, portal):
        portal.acl_users.source_users.addUser("test", "test", "test")
        
        portal.acl_users.manage_addProduct['NoDuplicateLogin'].manage_addNoDuplicateLogin("nodupe")
        portal.acl_users.plugins.activatePlugin(IAuthenticationPlugin, "nodupe")
        portal.acl_users.plugins.activatePlugin(ICredentialsResetPlugin, "nodupe")
        
        for i in range(10):
            # Make sure our plugin is first
            portal.acl_users.plugins.movePluginsUp(IAuthenticationPlugin, ["nodupe"])
            portal.acl_users.plugins.movePluginsUp(ICredentialsResetPlugin, ["nodupe"])
        
        import transaction
        transaction.commit()
    
    def tearDownZope(self, app):
        # Uninstall product
        z2.uninstallProduct(app, 'Products.NoDuplicateLogin')

NDL_ZOPE = z2.FunctionalTesting(bases=(NDL_FIXTURE, ), name='NDLFixture:Functional')
NDL_PLONE = ploneFunctionalTesting(bases=(NDLPlone(), ), name="NDLFixture:Plone")

class BasicAuthTests(unittest.TestCase):
    layer = NDL_ZOPE
    
    def setUp(self):
        app = self.layer['app']
        
        upgrade._replaceUserFolder(app)
        
        app.acl_users.users.addUser("test", "test", "test")
        
        app.acl_users.manage_addProduct['NoDuplicateLogin'].manage_addNoDuplicateLogin("nodupe")
        app.acl_users.plugins.activatePlugin(IAuthenticationPlugin, "nodupe")
        app.acl_users.plugins.activatePlugin(ICredentialsResetPlugin, "nodupe")
        app.acl_users.plugins.activatePlugin(ICredentialsUpdatePlugin, "nodupe")
        
        for i in range(10):
            # Make sure our auth plugin is first
            app.acl_users.plugins.movePluginsUp(IAuthenticationPlugin, ["nodupe"])
        
        import transaction
        transaction.commit()
        
    
    def test_anonymous_user_doesnt_generate_cookie(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.open(app.whoami.absolute_url())
        self.assertEqual(browser.contents, "Anonymous User")
        self.assertNotIn('__noduplicate', browser.cookies)
    
    def test_login_with_basic_auth_generates_cookie(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.addHeader("Authorization", "Basic " + "test:test".encode("base64"))
        browser.open(app.whoami.absolute_url())
        self.assertEqual(browser.contents, "test")
        self.assertIn('__noduplicate', browser.cookies)

    def test_second_attempt_at_basic_auth_generates_different_cookie(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.addHeader("Authorization", "Basic " + "test:test".encode("base64"))
        browser.open(app.whoami.absolute_url())
        self.assertEqual(browser.contents, "test")
        nodupe = browser.cookies['__noduplicate']
        
        second_browser = z2.Browser(app)
        second_browser.addHeader("Authorization", "Basic " + "test:test".encode("base64"))
        second_browser.open(app.whoami.absolute_url())
        self.assertEqual(second_browser.contents, "test")
        self.assertNotEqual(nodupe, second_browser.cookies['__noduplicate'])
        
    def test_second_attempt_at_basic_auth_invalidates_first_session(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.addHeader("Authorization", "Basic " + "test:test".encode("base64"))
        browser.open(app.whoami.absolute_url())
        self.assertEqual(browser.contents, "test")
        
        second_browser = z2.Browser(app)
        second_browser.addHeader("Authorization", "Basic " + "test:test".encode("base64"))
        second_browser.open(app.whoami.absolute_url())
        self.assertEqual(second_browser.contents, "test")
        
        browser.open(app.whoami.absolute_url())
        self.assertEqual(browser.contents, "Anonymous User")


class SessionTests(unittest.TestCase):
    layer = NDL_PLONE
    

    
    def test_anonymous_user_doesnt_generate_cookie(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url())
        self.assertIn("anon-personalbar", browser.contents)
        self.assertNotIn('__noduplicate', browser.cookies)
    
    def test_login_with_plone_session_generates_cookie(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = "test"
        login_form.getControl(name="__ac_password").value="test"
        login_form.submit()
        
        self.assertIn('<a id="user-name" href="http://nohost/plone/useractions">test</a>', browser.contents)
        self.assertIn('__noduplicate', browser.cookies)
        self.assertIn('__ac', browser.cookies)

    def test_second_attempt_at_login_generates_different_cookie(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = "test"
        login_form.getControl(name="__ac_password").value="test"
        login_form.submit()
        self.assertIn('<a id="user-name" href="http://nohost/plone/useractions">test</a>', browser.contents)
        nodupe = browser.cookies['__noduplicate']
        
        second_browser = z2.Browser(app)
        second_browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = second_browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = "test"
        login_form.getControl(name="__ac_password").value="test"
        login_form.submit()
        self.assertIn('<a id="user-name" href="http://nohost/plone/useractions">test</a>', browser.contents)
        self.assertNotEqual(nodupe, second_browser.cookies['__noduplicate'])
        
    def test_second_attempt_at_login_invalidates_first_session(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = "test"
        login_form.getControl(name="__ac_password").value="test"
        login_form.submit()
        
        second_browser = z2.Browser(app)
        second_browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = second_browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = "test"
        login_form.getControl(name="__ac_password").value="test"
        login_form.submit()
        self.assertIn('<a id="user-name" href="http://nohost/plone/useractions">test</a>', browser.contents)
                
        browser.open(self.layer['portal'].absolute_url())
        self.assertIn("anon-personalbar", browser.contents)
        self.assertNotIn('<a id="user-name" href="http://nohost/plone/useractions">test</a>', browser.contents)
        self.assertIn("Someone else logged in under your name. You have been logged out", browser.contents)
    
    def test_utility_method_invalidates_session(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = "test"
        login_form.getControl(name="__ac_password").value="test"
        login_form.submit()
        
        self.layer['portal'].acl_users.nodupe.logUserOut("test")
        import transaction
        transaction.commit()
                
        browser.open(self.layer['portal'].absolute_url())
        self.assertIn("anon-personalbar", browser.contents)
        self.assertNotIn('<a id="user-name" href="http://nohost/plone/useractions">test</a>', browser.contents)
        self.assertIn("An administrator has ended your session.", browser.contents)

class AdministratorRevokeTests(unittest.TestCase):
    layer = NDL_PLONE
    
    def setUp(self):
        # Make some changes
        setRoles(self.layer['portal'], "test", ['Manager'])
        # Commit so that the test browser sees these changes
        import transaction
        transaction.commit()
    
    def test_user_list_empty_without_active_users(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.addHeader('Authorization', 'Basic %s:%s' % ("test", "test",))
        
        # Simulate not being able to see anyone, as othewise there'll always be yourself in the
        # list of revokable sessions
        from Products.NoDuplicateLogin.views import RevokeSession
        old_visible_sessions = RevokeSession.visible_sessions
        try:
            RevokeSession.visible_sessions = lambda self: []
            browser.open(self.layer['portal'].acl_users.nodupe.absolute_url()+"/revoke_session")
        finally:
            RevokeSession.visible_sessions = old_visible_sessions
        
        self.assertIn("No sessions currently active", browser.contents)

    def test_logged_user_shown(self):
        app = self.layer['app']
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = "test"
        login_form.getControl(name="__ac_password").value="test"
        login_form.submit()
        
        browser = z2.Browser(app)
        browser.addHeader('Authorization', 'Basic %s:%s' % ("test", "test",))
        browser.open(self.layer['portal'].acl_users.nodupe.absolute_url()+"/revoke_session")
        users_info = re.compile(r"""<td>(.*?)</td>+""", re.I|re.M|re.X).findall(browser.contents)
                
        self.assertEqual(len(users_info), 2) # (username, time)
        self.assertEqual(users_info[0], "test")

    def test_cancelled_user_not_shown(self):
        app = self.layer['app']
        
        # Log in as 'test-user', a normal user
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = TEST_USER_NAME
        login_form.getControl(name="__ac_password").value=TEST_USER_PASSWORD
        login_form.submit()
        
        # Open the revoke page as the 'test' user, a Manager
        admin_browser = z2.Browser(app)
        admin_browser.addHeader('Authorization', 'Basic %s:%s' % ("test", "test",))
        admin_browser.open(self.layer['portal'].acl_users.nodupe.absolute_url()+"/revoke_session")
        
        # See we have two sessions available to cancel
        users_info = re.compile(r"""<td>(.*?)</td>+""", re.I|re.M|re.X).findall(admin_browser.contents)
        self.assertEqual(len(users_info), 4) # (username, time)
        
        # Cancel the session belonging to test-user
        test_user_index = users_info.index("test-user")//2
        admin_browser.getForm(index=test_user_index+1).submit() # Offset because of search form
        
        # We only have one user now
        users_info = re.compile(r"""<td>(.*?)</td>+""", re.I|re.M|re.X).findall(admin_browser.contents)
        self.assertEqual(len(users_info), 2)
    
    def test_logged_out_user_not_shown(self):
        app = self.layer['app']
        
        # Log in as 'test-user', a normal user
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = TEST_USER_NAME
        login_form.getControl(name="__ac_password").value=TEST_USER_PASSWORD
        login_form.submit()
        
        # Open the revoke page as the 'test' user, a Manager
        admin_browser = z2.Browser(app)
        admin_browser.addHeader('Authorization', 'Basic %s:%s' % ("test", "test",))
        admin_browser.open(self.layer['portal'].acl_users.nodupe.absolute_url()+"/revoke_session")
        
        # See we have two sessions available to cancel
        users_info = re.compile(r"""<td>(.*?)</td>+""", re.I|re.M|re.X).findall(admin_browser.contents)
        self.assertEqual(len(users_info), 4) # (username, time)
        
        # As the user, log out normally
        browser.getLink("Log out").click()
        
        # Check if the user is gone
        admin_browser.open(self.layer['portal'].acl_users.nodupe.absolute_url()+"/revoke_session")
        
        # We only have one user now
        users_info = re.compile(r"""<td>(.*?)</td>+""", re.I|re.M|re.X).findall(admin_browser.contents)
        self.assertEqual(len(users_info), 2)
    
    def test_cannot_invalidate_session_if_user_isnt_in_approved_list(self):
        app = self.layer['app']
        
        # Log in as 'test-user', a normal user
        browser = z2.Browser(app)
        browser.open(self.layer['portal'].absolute_url() + "/login")
        login_form = browser.getForm(id="login_form")
        login_form.getControl(name="__ac_name").value = TEST_USER_NAME
        login_form.getControl(name="__ac_password").value=TEST_USER_PASSWORD
        login_form.submit()
        
        # Open the revoke page as the 'test' user, a Manager
        admin_browser = z2.Browser(app)
        admin_browser.addHeader('Authorization', 'Basic %s:%s' % ("test", "test",))
        admin_browser.open(self.layer['portal'].acl_users.nodupe.absolute_url()+"/revoke_session")
        
        # See we have two sessions available to cancel
        users_info = re.compile(r"""<td>(.*?)</td>+""", re.I|re.M|re.X).findall(admin_browser.contents)
        self.assertEqual(len(users_info), 4) # (username, time) *2
        
        # Attempt to cancel the session belonging to test-user, but patch the view to remove that
        # user from being revocable before calling it. This simulates a falsified request by a 
        # semi-trusted user.
        from Products.NoDuplicateLogin.views import RevokeSession
        old_visible_sessions = RevokeSession.visible_sessions
        try:
            RevokeSession.visible_sessions = lambda self: []
            test_user_index = users_info.index("test-user")//2
            admin_browser.getForm(index=test_user_index+1).submit() # Offset because of search form
        finally:
            RevokeSession.visible_sessions = old_visible_sessions
        
        # Reload the page, we still have everyone
        admin_browser.open(self.layer['portal'].acl_users.nodupe.absolute_url()+"/revoke_session")
        users_info = re.compile(r"""<td>(.*?)</td>+""", re.I|re.M|re.X).findall(admin_browser.contents)
        self.assertEqual(len(users_info), 4) # (username, time) *2
