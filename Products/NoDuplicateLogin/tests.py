import unittest

from plone.testing import Layer
from plone.testing import z2
from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from Products.PluggableAuthService.Extensions import upgrade

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
            upgrade._replaceUserFolder(app)
            
            app.acl_users.users.addUser("test", "test", "test")
            
            app.acl_users.manage_addProduct['NoDuplicateLogin'].manage_addNoDuplicateLogin("nodupe")
            app.acl_users.plugins.activatePlugin(IAuthenticationPlugin, "nodupe")
            app.acl_users.plugins.activatePlugin(ICredentialsResetPlugin, "nodupe")
            
            for i in range(10):
                # Make sure our plugin is first
                app.acl_users.plugins.movePluginsUp(IAuthenticationPlugin, ["nodupe"])
                app.acl_users.plugins.movePluginsUp(ICredentialsResetPlugin, ["nodupe"])
            
            app.manage_addProduct['PythonScripts'].manage_addPythonScript("whoami")
            whoami = app.whoami
            whoami.write(WHOAMI_SCRIPT)
        

NDL_FIXTURE = NDLFixture()
NDL_FUNCTIONAL = z2.FunctionalTesting(bases=(NDL_FIXTURE, ), name='NDLFixture:Functional')

class BasicAuthTests(unittest.TestCase):
    layer = NDL_FUNCTIONAL
    
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
        nodupe = browser.cookies['__noduplicate']
        
        second_browser = z2.Browser(app)
        second_browser.addHeader("Authorization", "Basic " + "test:test".encode("base64"))
        second_browser.open(app.whoami.absolute_url())
        self.assertEqual(second_browser.contents, "test")
        
        browser.open(app.whoami.absolute_url())
        self.assertEqual(browser.contents, "Anonymous User")
