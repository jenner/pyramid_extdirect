import os

from setuptools import setup, find_packages

import pyramid_extdirect

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = ['pyramid', 'venusian']

setup(name='pyramid_extdirect',
    version=pyramid_extdirect.__version__,
    description='ExtDirect Implementation for pyramid',
    long_description=README + '\n\n' +  CHANGES,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: BFG",
        "License :: Repoze Public License",
    ],
    keywords='web wsgi javascript pyramid extdirect',
    author="Igor Stroh",
    author_email="igor.stroh@rulim.de",
    url="http://github.com/jenner/repoze.bfg.extdirect",
    license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    tests_require=requires,
    install_requires=requires,
    entry_points="""\
    """
)
