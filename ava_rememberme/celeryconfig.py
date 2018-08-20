from celery.schedules import crontab

# Broker settings.
broker_url = 'redis://localhost'

# List of modules to import when the Celery worker starts.
# imports = ('myapp.tasks',)

# Using the database to store task state and results.
result_backend = 'redis://'

# Timezone
timezone = 'America/Sao_Paulo'
""" There are mainly three activities that should happen.

Refresh disciplines: Once per month should be sufficient for checking
if a user has a new discipline. Note that this is very rare.

Refresh assignments: Once per week or Once in two weeks to save some
processing.

Check due dates: This should happen once per day, since it is the main
pourpose of this app. :)

"""

beat_schedule = {
    'refresh-disciplines': {
        'task':
        'ava_rememberme.tasks.databaseRefreshDisciplines',
        'schedule':
        crontab(minute='0', hour='3', day_of_month='1-7', day_of_week='0')
    }
}
