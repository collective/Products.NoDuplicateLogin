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
#   * Neither the name of Archetypes nor the names of its contributors
#     may be used to endorse or promote products derived from this
#     software without specific prior written permission. 
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

"""NoDuplicateLogin doctests (requires Plone)
"""

__author__ = "Daniel Nouri <daniel.nouri@gmail.com>"

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import doctest
import unittest
from Testing.ZopeTestCase import FunctionalDocFileSuite, FunctionalDocTestSuite
from Products.PloneTestCase import PloneTestCase

PloneTestCase.installProduct('PluginRegistry')
PloneTestCase.installProduct('PluggableAuthService')
PloneTestCase.installProduct('PlonePAS')
PloneTestCase.installProduct('PasswordResetTool')
PloneTestCase.installProduct('NoDuplicateLogin')
PloneTestCase.setupPloneSite(products=['PlonePAS'])

def test_suite():
    return unittest.TestSuite((
        FunctionalDocFileSuite('browser.txt',
                               optionflags = doctest.REPORT_ONLY_FIRST_FAILURE,
                               package='Products.NoDuplicateLogin.tests',
                               test_class=PloneTestCase.FunctionalTestCase),
        ))

if __name__ == '__main__':
    framework()

