
from setuptools import setup, find_packages

def read(filename):
    return open(filename, 'rb').read()

setup(
    version='1.0a2',
    name='Products.NoDuplicateLogin',
    description='Products.NoDuplicateLogin',
    long_description=read('README.txt') + read('docs/HISTORY.txt'),
    author='Daniel Nouri',
    author_email='daniel.nouri@gmail.com',
    url='http://svn.plone.org/svn/collective/PASPlugins/Products.NoDuplicateLogin',
    namespace_packages=['Products'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Plone',
        'setuptools',
        ],
    extras_require={
        'tests': ['zope.testing'],
    },
    )
