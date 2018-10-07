from setuptools import setup

setup(
    name='ava_rememberme',
    packages=['ava_rememberme'],
    version='0.1.0',
    author='Martin Mariano',
    author_email='contato@martinmariano.com',
    include_package_data=True,
    install_requires=[
        'flask', 'flask-security', 'flask-sqlalchemy', 'beautifulsoup4',
        'selenium', 'celery[redis]', 'requests', 'lxml', 'flask-babel',
        'flask-migrate', 'gunicorn'
    ],
    extras_require={'psql': ['psycopg2'], 'monitoring': ['flower']})
