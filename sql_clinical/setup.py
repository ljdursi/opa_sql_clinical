#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

requirements = []
setup_requirements = ['pytest-runner', ]
test_requirements = ['pytest', ]

setup(
    author="Jonathan Dursi",
    author_email='jonathan@dursi.ca',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="OPA-wrapped SQL data filtering",
    install_requires=requirements,
    license="GNU General Public License v3",
    include_package_data=True,
    keywords='sql_clinical',
    name='sql_clinical',
    packages=find_packages(include=['sql_clinical']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/CanDIG/opa_sql_clinical',
    version='0.1.1',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'sql_clinical = sql_clinical.service:main'
            ]
        },
)
