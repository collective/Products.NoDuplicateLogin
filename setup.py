
from setuptools import setup, find_packages

setup(
    version='1.0a1',
    name='Products.NoDuplicateLogin',
    author='Daniel Nouri',
    author_email='daniel.nouri@gmail.com',
    namespace_packages=['Products'],
    packages=find_packages(),
    install_requires=[
        'setuptools',
        ]
    )
