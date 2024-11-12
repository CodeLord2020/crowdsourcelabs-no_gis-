# cddp/celery.py
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cddp.settings')

app = Celery('cddp', include=['cddp.tasks'])

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configure Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'check-overdue-tasks': {
        'task': 'cddp.tasks.check_overdue_tasks',
        'schedule': 300.0,  # every 5 minutes
    },
    'test_stuff': {
        'task': 'cddp.tasks.test_stuff',
        'schedule': 300.0,  # every 5 minutes
    },
    'send-task-reminders': {
        'task': 'cddp.tasks.send_task_reminders',
        'schedule': 3600.0,  # every hour
    },

}

# Optional configuration
# app.conf.update(
#     worker_max_tasks_per_child=1000,
#     worker_prefetch_multiplier=1,
#     task_time_limit=3600,  # 1 hour
#     task_soft_time_limit=3000,  # 50 minutes
#     task_default_queue='default',
#     task_queues={
#         'default': {},
#         'email': {
#             'routing_key': 'email.#',
#         },
#         'high_priority': {
#             'routing_key': 'high.#',
#         },
#     }
# )


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')



#COMMANDS
# Start Celery worker
# celery -A cddp worker --beat --loglevel=info

# Or, if you want to run the worker and beat as separate processes:
# celery -A cddp worker --loglevel=info
# celery -A cddp beat --loglevel=info