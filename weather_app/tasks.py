import logging
from datetime import datetime

import pytz
from celery import shared_task
from django.core.mail import send_mail
from redis import Redis

from .models import Subscription
from .views import get_weather

REDIS_HOST = 'redis'
REDIS_PORT = 6379
redis = Redis(host=REDIS_HOST, port=REDIS_PORT)

logger = logging.getLogger(__name__)

local_timezone = pytz.timezone('Europe/Kiev')


@shared_task
def subscribed_city_beat():
    subscribed_city = Subscription.objects.all()
    for el in subscribed_city:
        time = datetime.now(tz=local_timezone) - el.updated_at
        hours = time.days * 24

        if hours >= el.period_of_notification:
            weather = get_weather(el.city.city_name)
            weather_data = f'Temperature {weather["temperature"]}\nDescription {weather["description"]}\nHumidity {weather["humidity"]}\nWind speed {weather["wind_speed"]}'

            send_email_task.delay(el.user.email, el.city.city_name, weather_data)
            el.updated_at = datetime.now(tz=local_timezone)
            el.save()
        else:
            logger.info(f'Skipping sending weather data for {el.city.city_name} because the period of notification has not expired yet.')


@shared_task
def send_email_task(email, city_name, weather_data):
    send_mail(
        f'Weather notification in {city_name}',
        weather_data,
        'sk.anton06@gmail.com',
        [email],
        fail_silently=False,
    )
