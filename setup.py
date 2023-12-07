
from setuptools import setup, find_packages

def read(filename):
    return open(filename, 'rb').read()

setup(
    version='3.0.0a1',
    name='Products.NoDuplicateLogin',
    description='Products.NoDuplicateLogin',
    long_description=read('README.rst')
                   + read('docs/CONTRIBUTING.rst')
                   + read('docs/HISTORY.rst'),
    long_description_content_type='text/x-rst',
    author='Daniel Nouri',
    author_email='daniel.nouri@gmail.com',
    project_urls={
        'Documentation': 'https://pypi.org/project/Products.NoDuplicateLogin',
        'Source': 'https://github.com/collective/Products.NoDuplicateLogin',
        'Tracker': 'https://github.com/collective/Products.NoDuplicateLogin/issues',
        },
    # Get more from https://pypi.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        'Framework :: Zope2',
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        'Intended Audience :: System Administrators',
        "Operating System :: OS Independent",
    ],
    namespace_packages=['Products'],
    packages=find_packages(),
    include_package_data=True,
    # used by setuptools as of v24.0.0:
    python_requires='>=2.5',  # 2.5+: hashlib; TODO: other requirements?
    install_requires=[
        'setuptools',
        'six',  # early releases support Python 2.5+
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
