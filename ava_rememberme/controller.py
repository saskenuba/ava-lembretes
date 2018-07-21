from celery import Celery


def create_celery(app):
    celery = Celery(app.name)
    celery.config_from_object('ava_rememberme.celeryconfig')

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
