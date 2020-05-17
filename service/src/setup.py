import os
import subprocess


from setuptools import setup
from setuptools import find_packages
packages = find_packages()

setup(
    name='ooonline',
    version='0.01',
    packages=packages,
    install_requires=[
        'flask',
        'flask-restful',
        'flask-HTTPAuth',
        'itsdangerous',
        'sqlalchemy',
        'Flask-SQLAlchemy',
        'psycopg2',
    ],
    dependency_links=[
    ],
)
