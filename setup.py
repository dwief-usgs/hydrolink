#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Daniel J Wieferich",
    author_email='dwieferich@usgs.gov',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: unlicense',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python package with methods to address information to National Hydrography Datasets",
    install_requires=requirements,
    license="unlicense",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='hydrolink',
    name='hydrolink',
    packages=find_packages(include=['hydrolink', 'hydrolink.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/dwief-usgs/hydrolink',
    version='0.0.4',
    zip_safe=False,
)
