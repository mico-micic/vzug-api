import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "README.md"), encoding="utf-8") as readme:
    long_description = readme.read()

setup(
    name='vzug-api',
    description='V-ZUG API library',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'aiohttp>=3.8.0',
        'tenacity>=8.0.0',
        'yarl>=1.7.0'
    ],
    tests_require=['pytest'],
    url='',
    license='GNU General Public License v3.0',
    author='Mico Micic',
    author_email='mico@micic.ch'
)
