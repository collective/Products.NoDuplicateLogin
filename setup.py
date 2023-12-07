
from setuptools import setup, find_packages

def read(filename):
    return open(filename, 'rb').read()

setup(
    version='2.0.1',
    name='Products.NoDuplicateLogin',
    description='Products.NoDuplicateLogin',
    long_description=read('README.txt')
                   + read('docs/CONTRIBUTING.rst')
                   + read('docs/HISTORY.txt'),
    long_description_content_type='text/x-rst',
    author='Daniel Nouri',
    author_email='daniel.nouri@gmail.com',
    project_urls={
        'Documentation': 'https://pypi.org/project/Products.NoDuplicateLogin',
        'Source': 'https://github.com/collective/Products.NoDuplicateLogin',
        'Tracker': 'https://github.com/collective/Products.NoDuplicateLogin/issues',
        },
    namespace_packages=['Products'],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'setuptools',
        'collective.autopermission',
        ],
    extras_require={
        'tests': [
                'plone.app.testing',
            ],
    	},
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
)
