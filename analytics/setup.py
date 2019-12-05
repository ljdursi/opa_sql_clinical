#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

requirements = []
setup_requirements = ['pytest-runner', ]
test_requirements = ['pytest', ]

data_files = [('api', ['analytics_service/api/swagger.yaml'])]

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
    keywords='analytics_service',
    name='analytics_service',
    packages=find_packages(include=['analytics_service']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    data_files=data_files,
    url='https://github.com/CanDIG/opa_sql_clinical',
    version='0.1.1',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'analytics_service = analytics_service.__main__:main'
            ]
        },
)
