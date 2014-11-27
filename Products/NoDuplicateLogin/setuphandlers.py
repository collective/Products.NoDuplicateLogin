from Products.PluggableAuthService.interfaces.plugins import IAuthenticationPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsResetPlugin
from Products.PluggableAuthService.interfaces.plugins import ICredentialsUpdatePlugin

def setupVarious(context):
    """
    @param context: Products.GenericSetup.context.DirectoryImportContext instance
    """

    # We check from our GenericSetup context whether we are running
    # add-on installation for your product or any other proudct
    if context.readDataFile('noduplicatelogin.xml') is None:
        # Not your add-on
        return

    portal = context.getSite()
    
    portal.acl_users.manage_addProduct['NoDuplicateLogin'].manage_addNoDuplicateLogin("unique_sessions")
    portal.acl_users.plugins.activatePlugin(IAuthenticationPlugin, "unique_sessions")
    portal.acl_users.plugins.activatePlugin(ICredentialsResetPlugin, "unique_sessions")
    portal.acl_users.plugins.activatePlugin(ICredentialsUpdatePlugin, "unique_sessions")
    
    for i in range(10):
        # Make sure our auth plugin is first
        portal.acl_users.plugins.movePluginsUp(IAuthenticationPlugin, ["unique_sessions"])
    