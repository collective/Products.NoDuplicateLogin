NoDuplicateLogin

  This Pluggable Authentication Service (PAS) plugin will reject multiple 
  logins with the same user at the same time.  That is, it ensures that 
  only one browser may be logged with the same userid at one time.

Requires:

 - PluggableAuthService and its dependencies

 - (optional) PlonePAS and its dependencies


Installation

  Place the Product directory 'NoDuplicateLogin' in your 'Products/'
  directory. Restart Zope.

  In your PAS 'acl_users', select 'NoDuplicateLogin' from the add
  list.  Give it an id and title, and push the add button.

  Enable the 'Authentication' and the 'Credentials Reset' plugin
  interfaces in the after-add screen.

  Rearrange the order of your 'Authentication Plugins' so that the
  'NoDuplicateLogin' plugin is at the top.

  That's it! Test it out.


Implementation

  The implementation works like this: Suppose that Anna and Karl are
  two people who share a login 'annaandkarl' in our site.  Anna logs
  in, authenticating for the first time.  We generate a cookie with a
  unique id for Anna and remember the id ourselves.  For every
  subsequent authentication (i.e. for every request), we will make
  sure that Anna's browser has the cookie.

  Now Karl decides to log in into the site with the same login
  'annaandkarl', the one that Anna uses to surf the site right now.
  The plugin sees that Karl's browser doesn't have our cookie yet, so
  it generates one with a unique id for Karl's browser, remembers it
  and *forgets* about Anna's cookie.

  What happens when Anna clicks on a link on the site?  The plugin
  sees that Anna has our cookie but that it differs from the cookie
  value that it remembered (Karl's browser has that cookie value).
  Anna is logged out but the plugin and sees the message "Someone else
  logged in under your name".

  The default implementation uses a cookie as described above.  This
  should be good enough in most cases, however, it means that you can
  easily hack the mechanism if you know how it works by simply setting
  the same cookie value in both browsers.  The plugin comes with an
  experimental session-based mechanism, which you can activate by
  ticking "session based" in the plugin's properties form.


Copyright, License, Author

  Copyright (c) 2006, BlueDynamics, Klein & Partner KEG, Innsbruck,
  Austria, and the respective authors. All rights reserved.
 
  Author: Daniel Nouri <daniel.nouri@gmail.com>

  License BSD-ish, see LICENSE.txt


Credits

  Thanks to James Cameron Cooper and Enfold Systems for their
  GMailAuthPlugin which served as the base for this.
