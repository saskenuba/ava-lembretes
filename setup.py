from setuptools import setup

setup(
    name='ava_rememberme',
    packages=['ava_rememberme'],
    author='Martin Mariano',
    author_email='contato@martinmariano.com',
    include_package_data=True,
    install_requires=[
        'flask', 'flask-security', 'flask-sqlalchemy', 'beautifulsoup4', 'selenium', 'celery[redis]'

    ],
    extras_require={
        'psql': ['psycopg2']
    }
)
