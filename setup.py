import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, "README_PYPI.md"), encoding="utf-8") as readme:
    long_desc = readme.read()

setup(
    name='vzug-api',
    version='0.1.1',
    description='Unofficial python API for V-ZUG devices',
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url='https://github.com/mico-micic/vzug-api',
    author='Mićo Mićić',
    author_email='mico@micic.ch',
    license='GNU General Public License v3.0',
    packages=find_packages(exclude=["test", "examples"]),
    include_package_data=True,
    install_requires=[
        'aiohttp>=3.8.0',
        'tenacity>=8.0.0',
        'yarl>=1.7.0'
    ],
    tests_require=['pytest', 'flask', 'flask_httpauth', 'Flask-Testing'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.8",
        "Topic :: Home Automation",
    ],
)
