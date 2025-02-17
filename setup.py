#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='sparkbasics',
    version='1.0.0',
    description='BDCC Pyspark Basics project',
    py_modules=['__main__'],
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=False
)
