import unittest

from plone.testing import Layer
from plone.testing import z2

class NDLFixture(Layer):
    defaultBases = (z2.STARTUP,)

NDL_FIXTURE = NDLFixture()
NDL_FUNCTIONAL = z2.FunctionalTesting(bases=(NDL_FIXTURE, ), name='NDLFixture:Functional')

class DoStuffWithUnitTest(unittest.TestCase):
    layer = NDL_FUNCTIONAL
    
    def testFoo(self):
        self.assertEqual(1, 2)

