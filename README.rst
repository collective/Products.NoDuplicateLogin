.. image::
   https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336
       :target: https://pycqa.github.io/isort/

Introduction
============

This PAS plugin will reject multiple logins with the same user at the same
time. It ensures that only one browser may be logged with the same userid at
one time.

Implementation
--------------

The implementation works like this: Suppose that Anna and Karl are two people
who share a login annaandkarl in our site. Anna logs in, authenticating for
the first time. We generate a cookie with a unique id for Anna and remember
the id ourselves. For every subsequent authentication (i.e. for every
request), we will make sure that Anna's browser has the cookie.

Now Karl decides to log in into the site with the same login annaandkarl, the
one that Anna uses to surf the site right now. The plugin sees that Karl's
browser doesn't have our cookie yet, so it generates one with a unique id for
Karl's browser, remembers it and forgets about Anna's cookie.

What happens when Anna clicks on a link on the site? The plugin sees that Anna
has our cookie but that it differs from the cookie value that it remembered
(Karl's browser has that cookie value). Anna is logged out but the plugin and
sees the message "Someone else logged in under your name".

.. Warning::

    Because this implementation stores its mappings in the ZODB on attributes
    of the plugin itself, there may be issues with scaling.

Installation
------------

Add ``Products.NoDuplicateLogin`` to the eggs parameter of your ``plone.recipe.zope2instance``
section::

    [plone]
    recipe = plone.recipe.zope2instance
    eggs =
        Plone
        ...
        Products.NoDuplicateLogin

Now run buildout and restart Plone. Once Plone has started, login and browse
to ``Site Setup -> Zope Management Interface -> acl_users`` and add a ``No Duplicate
Login Plugin`` from the drop down menu in the upper right.

After that, click on the ``No Duplicate Login Plugin`` object in the acl_users
folder listing. For both the ``Authentication`` and ``Reset Credentials``
objects in the ``No Duplicate Login Plugin`` folder listing, click, then move the
``no_duplicate_login`` plugin from the ``Available Plugins`` display widget on the
left to the ``Active Plugins`` display widget on the right using the arrow
buttons in the middle.

Now test! It may also be necessary to "arrow up" the ``no_duplicate_login``
plugin in the ``Active Plugins`` display listing for both ``Authentication``
and ``Reset Credentials``.

If you are using a policy product to install this, you can perform these actions by including an
empty ``noduplicatelogin.xml`` file in your profile directory.
