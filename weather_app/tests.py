import os
from datetime import datetime, timedelta

import django
import pytz

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "DjangoWeatherReminder.settings")
django.setup()

from unittest.mock import MagicMock
from weather_app.models import Subscription, User, City

from django.test import TestCase
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch

from weather_app.tasks import send_email_task, subscribed_city_beat

local_timezone = pytz.timezone('Europe/Kiev')


class TestViews(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.get_weather_url = 'DjangoWeatherReminder:city_weather'
        self.register_user_url = 'DjangoWeatherReminder:register'
        self.subscriptions_url = 'DjangoWeatherReminder:subscriptions'
        self.update_subscription_url = 'DjangoWeatherReminder:update_subscription'
        self.delete_subscription_url = 'DjangoWeatherReminder:delete_subscription'

    def test_get_valid_weather(self):
        url = reverse(self.get_weather_url, kwargs={'city_name': 'Kharkiv'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch('weather_app.views.get_weather')
    def test_get_not_valid_weather(self, mock_get_weather):
        # empty data means serializer validation error
        mock_get_weather.return_value = {}
        url = reverse(self.get_weather_url, kwargs={'city_name': 'Kkk'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_register_user(self):
        url = reverse(self.register_user_url)
        data = {
            'username': 'TomUser',
            'email': 'Tom@gmail.com',
            'password': '1234Password1234',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=data['email'])
        self.assertTrue(user.check_password(data['password']))

    def test_not_valid_password_register_user(self):
        url = reverse(self.register_user_url)
        data = {
            'username': 'admin',
            'email': 'Tom@gmail.com',
            'password': '1234',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_for_user(self):
        # firstly, create a user
        data = {
            'username': 'TomUser',
            'email': 'Tom@gmail.com',
            'password': '1234Password1234',
        }
        response = self.client.post(reverse('DjangoWeatherReminder:register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # secondly, get an access token for created user
        data = {'username': 'TomUser', 'password': '1234Password1234'}
        response = self.client.post(reverse('DjangoWeatherReminder:token_obtain_pair'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        return response.data["access"]

    def test_get_subscriptions_unauthorized(self):
        url = reverse(self.subscriptions_url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_subscriptions_authorized(self):
        url = reverse(self.subscriptions_url)
        # providing access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {TestViews.test_create_token_for_user(self)}')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_subscription(self):
        url = reverse(self.update_subscription_url, kwargs={'city_name': 'London', 'period_of_notification': 2})
        # providing access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {TestViews.test_create_token_for_user(self)}')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['period_of_notification'], 2)
        self.assertIsInstance(response.data['period_of_notification'], int)
        self.assertIsInstance(response.data['city'], int)

    def test_update_subscription(self):
        # providing access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {TestViews.test_create_token_for_user(self)}')
        # creating a subscription
        create_url = reverse(self.update_subscription_url, kwargs={'city_name': 'London', 'period_of_notification': 2})
        self.client.post(create_url)

        # updating period of notification
        update_url = reverse(self.update_subscription_url, kwargs={'city_name': 'London', 'period_of_notification': 12})
        response = self.client.put(update_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['period_of_notification'], 12)

    def test_delete_subscription(self):
        # providing access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {TestViews.test_create_token_for_user(self)}')
        # creating a subscription
        create_url = reverse(self.update_subscription_url, kwargs={'city_name': 'London', 'period_of_notification': 2})
        self.client.post(create_url)

        # deleting a subscription
        delete_url = reverse(self.delete_subscription_url, kwargs={'city_name': 'London'})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, 'Subscription has been deleted')


class TestCeleryTasks(TestCase):
    @patch('weather_app.tasks.send_mail')
    def test_send_email_task(self, mock_send_mail):
        email = 'test@example.com'
        city_name = 'London'
        weather_data = 'Temperature: 70F\nDescription: Sunny\nHumidity: 50%\nWind Speed: 10mph'

        send_email_task(email, city_name, weather_data)

        # checks that the mock_send_mail was called once with the arguments
        mock_send_mail.assert_called_once_with(
            f'Weather notification in {city_name}',
            weather_data,
            'sk.anton06@gmail.com',
            [email],
            fail_silently=False,
        )


class SubscribedCityBeatTestCase(TestCase):
    def setUp(self):
        # create a user
        self.test_user = User.objects.create(
            username='test_username',
            email='test_user@test.com',
            password='Test_user_password_0123',
        )

        # create a city
        self.city = City.objects.create(city_name='Paris')

        # create a test subscription
        self.test_subscription = Subscription.objects.create(
            user_id=self.test_user.id,
            city_id=self.city.id,
            period_of_notification=12,
            updated_at=datetime.now(tz=local_timezone),
        )

    @patch('weather_app.tasks.get_weather')
    @patch('weather_app.tasks.send_email_task.delay')
    def test_subscribed_city_beat(self, mock_send_email_task_delay, mock_get_weather):
        weather_data = {
            'temperature': 9,
            'description': 'Mostly cloudy',
            'humidity': 91,
            'wind_speed': 3,
        }
        # mock weather data that are returned from get_weather function
        mock_get_weather.return_value = weather_data

        # mock data for sending email
        mock_send_email_task = MagicMock()
        # mock return value from send email function
        mock_send_email_task_delay.return_value = mock_send_email_task

        # update time to more than was written in SetUp (12 hours)
        self.test_subscription.updated_at = datetime.now(tz=local_timezone) - timedelta(hours=24)
        self.test_subscription.save()

        # call subscribed_city_beat task
        subscribed_city_beat()

        # check that the mock was called once and with the arguments for get_weather
        mock_get_weather.assert_called_once_with(self.city.city_name)

        # mock was called once and with the arguments for send email
        mock_send_email_task_delay.assert_called_once_with(
            self.test_user.email,
            self.city.city_name,
            f'Temperature {weather_data["temperature"]}\nDescription {weather_data["description"]}\nHumidity {weather_data["humidity"]}\nWind speed {weather_data["wind_speed"]}'
        )
