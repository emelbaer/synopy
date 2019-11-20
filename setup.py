#!/usr/bin/env python

import os
import sys

from distutils.core import setup

setup(
    name='synopy',
    version='0.2.0',
    packages=['synopy'],
    url='https://github.com/gspanos/synopy',
    license='',
    author='George Spanos',
    author_email='spanosgeorge@gmail.com',
    description='Python library for the Synology DiskStation APIs',
    install_requires=[
   'requests>=2.20.0',
   'B>=2six>=1.12.0'
    ],
)
