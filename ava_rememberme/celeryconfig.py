from celery.schedules import crontab

# Broker settings.
broker_url = 'redis://localhost'

# List of modules to import when the Celery worker starts.
# imports = ('myapp.tasks',)

# Using the database to store task state and results.
result_backend = 'redis://'

# Timezone
timezone = 'America/Sao_Paulo'

beat_schedule = {
    'refresh-all-users': {
        'task': 'ava_rememberme.tasks.databaseRefreshAllUsers',
        'schedule': crontab(day_of_month='10,20,30'),
    },
    'subtract-day': {
        'task': 'ava_rememberme.tasks.databaseSubtractDay',
        'schedule': crontab(minute='59', hour='23'),
    }
}
