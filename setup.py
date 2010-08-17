__version__ = '0.1.2'

import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

setup(name='repoze.bfg.extdirect',
    version=__version__,
    description='ExtDirect Implementation for repoze',
    long_description=README + '\n\n' +  CHANGES,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: BFG",
        "License :: Repoze Public License",
    ],
    keywords='web wsgi javascript',
    author="Igor Stroh",
    author_email="igor.stroh@rulim.de",
    url="http://github.com/jenner/repoze.bfg.extdirect",
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['repoze', 'repoze.bfg'],
    zip_safe=False,
    tests_require=['repoze.bfg', 'venusian'],
    install_requires=['repoze.bfg', 'venusian'],
    test_suite="repoze.bfg.extdirect",
    entry_points="""\
    """
)
