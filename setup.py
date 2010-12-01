
from setuptools import setup, find_packages

setup(
    version='1.0 svn/dev',
    name='Products.NoDuplicateLogin',
    author='Jens Klein',
    author_email='jens@bluedynamics.com',
    namespace_packages=['Products'],
    packages=find_packages(),
    install_requires=[
        'setuptools',
        ]
    )
