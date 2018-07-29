from flask import Flask
from secrets import token_hex
from ava_rememberme.controller import create_celery

app = Flask(__name__)
app.config['SECRET_KEY'] = token_hex(32)
app.config['SERVER_NAME'] = 'localhost:5000'

celery = create_celery(app)

from ava_rememberme.database import init_db, engine
from ava_rememberme import views

init_db()
