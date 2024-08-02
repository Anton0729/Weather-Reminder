import os
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoWeatherReminder.settings')

app = Celery('DjangoWeatherReminder')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Set up Celery to use the Django settings module
# - namespace='CELERY' means all celery-related configuration keys /
app.config_from_object('django.conf:settings', namespace='CELERY')
