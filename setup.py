
from setuptools import setup, find_packages

def read(filename):
    return open(filename, 'rb').read()

setup(
    version='1.0a1',
    name='Products.NoDuplicateLogin',
    description='Products.NoDuplicateLogin',
    long_description=read('README.txt') + read('docs/HISTORY.txt'),
    author='Daniel Nouri',
    author_email='daniel.nouri@gmail.com',
    namespace_packages=['Products'],
    packages=find_packages(),
    install_requires=[
        'setuptools',
        ]
    extras_require={
        'tests': ['zope.testing'],
    },
    )
