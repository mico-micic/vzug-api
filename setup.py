import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "readme.rst"), encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name='vzug-api',
    version='0.0.1',
    packages=[''],
    url='',
    license='GNU General Public License v3.0',
    author='Mico Micic',
    author_email='mico@micic.ch',
    description='V-ZUG API library'
)
