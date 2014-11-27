import unittest

from plone.app.testing import FunctionalTesting as ploneFunctionalTesting
from plone.app.testing import PLONE_FIXTURE
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
NDL_ZOPE = z2.FunctionalTesting(bases=(NDL_FIXTURE, ), name='NDLFixture:Functional')
NDL_PLONE = ploneFunctionalTesting(bases=(NDL_FIXTURE, PLONE_FIXTURE, ), name="NDLFixture:Plone")

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
    
    def setUp(self):
        app = self.layer['portal']
        app.acl_users.source_users.addUser("test", "test", "test")
        
        app.acl_users.manage_addProduct['NoDuplicateLogin'].manage_addNoDuplicateLogin("nodupe")
        app.acl_users.plugins.activatePlugin(IAuthenticationPlugin, "nodupe")
        app.acl_users.plugins.activatePlugin(ICredentialsResetPlugin, "nodupe")
        
        for i in range(10):
            # Make sure our plugin is first
            app.acl_users.plugins.movePluginsUp(IAuthenticationPlugin, ["nodupe"])
            app.acl_users.plugins.movePluginsUp(ICredentialsResetPlugin, ["nodupe"])
        
        import transaction
        transaction.commit()
    
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
