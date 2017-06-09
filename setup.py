#!/usr/bin/env python

from distutils.core import setup

setup(
    name='phila_taskflow',
    version='0.1dev',
    packages=[
        'phila_taskflow',
        'phila_taskflow.workflows',
        'phila_taskflow.workflows.etl',
        'phila_taskflow.tasks',
        'phila_taskflow.tasks.abstract'
    ],
    install_requires=[
    ],
    dependency_links=[
    ],
)
