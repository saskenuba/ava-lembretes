from flask import Flask
from secrets import token_bytes
from ava_rememberme.controller import create_celery

app = Flask(__name__)
app.config['SECRET_KEY'] = token_bytes(24)

celery = create_celery(app)

from ava_rememberme.database import init_db, engine
from ava_rememberme import views

init_db()
