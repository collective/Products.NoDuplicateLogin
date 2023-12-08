
History
-------

3.0.0 (unreleased)
~~~~~~~~~~~~~~~~~~

* Python 3 compatibility, using six_ [tobiasherp]
* Fix issue9_, The cleanUp method always reports 0 deleted entries [tobiasherp]


2.0.1 (2023-12-04)
~~~~~~~~~~~~~~~~~~

* Packaging bugfix: The plugin can't be added, due to missing add template
  [pigeonflight]


2.0 (2014-11-25)
~~~~~~~~~~~~~~~~

* Security and performance improvements [matthewwilkes]
* Remove reimplementation of plone.session [matthewwilkes]
* Change internal data structures to avoid unnecessary object stores [matthewwilkes]
* Add tests to test harness [matthewwilkes]
* Fix pure Zope compatibility [matthewwilkes]


1.0b1 (25/11/2014)
~~~~~~~~~~~~~~~~~~

* Remove reimplementation of plone.session [matthewwilkes]
* Change internal data structures to avoid unnecessary object stores [matthewwilkes]
* Add tests to test harness [matthewwilkes]
* Fix pure Zope compatibility [matthewwilkes]

1.0a2 (02/18/2011)
~~~~~~~~~~~~~~~~~~

* Add more installation instructions
       
1.0a1 (12/17/2010)
~~~~~~~~~~~~~~~~~~

* Add test harness [aclark]
* Rip out "experimental" session storage, too many ZODB conflicts. [aclark]
* Plone 4 compat [aclark]
* Re-package as egg [aclark]

1.0 svn/dev
~~~~~~~~~~~

* Plone 3 compat [perrito]
* Original implementation [nouri]

.. _issue9: https://github.com/collective/Products.NoDuplicateLogin/issues/9
.. _six: https://pypi.org/project/six/
