#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='structattr',
    version='0.0.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    python_requires=">=3.6",
    install_requires=[
        'attrs>=17.3.0',
        'bitstruct',
    ],
    setup_requires=[
        'pytest-runner'
    ],
    tests_require=[
        'pytest',
    ],
)
