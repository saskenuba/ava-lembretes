from flask import Flask
from secrets import token_hex
from ava_rememberme.controller import create_celery
from flask_migrate import Migrate
from flask_babel import Babel

app = Flask(__name__)
app.config['SECRET_KEY'] = token_hex(32)
# app.config['SERVER_NAME'] = 'localhost:5000'

celery = create_celery(app)
babel = Babel(app, default_locale='br')

from ava_rememberme.database import init_db, engine, Base
from ava_rememberme import views

# init_db()
Migrate(app, db=Base)


@app.cli.command()
def create_db():
    Base.metadata.create_all()
