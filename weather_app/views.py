from datetime import datetime

import pytz
import requests
from django.db.utils import IntegrityError, OperationalError
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from retry import retry

from DjangoWeatherReminder.settings import OPEN_WEATHER_API_URL, OPEN_WEATHER_API_TOKEN
from .models import Subscription, City
from .serializers import RegisterSerializer, WeatherViewSerializer, SubscriptionsSerializer, UserSerializer

local_timezone = pytz.timezone('Europe/Kiev')


# check if city exists, create/get id
def city_exists(city_name):
    city_exists = City.objects.filter(city_name=city_name).exists()

    # if city doesn't exist
    if not city_exists:
        city = City.objects.create(city_name=city_name)
        city.save()
        return city

    # if city exists
    elif city_exists:
        return City.objects.get(city_name=city_name)


# getting weather by city name from openweathermap
def get_weather(city_name):
    # url where to make request
    url = f'{OPEN_WEATHER_API_URL}?q={city_name}&appid={OPEN_WEATHER_API_TOKEN}&units=metric'

    try:
        response = requests.get(url)
        # convert data to json format
        data = response.json()

        # write all necessary data to a dictionary
        weather_data = {
            'description': data['weather'][0]['description'],
            'temperature': data['main']['temp'],
            'temperature_min': data['main']['temp_min'],
            'temperature_max': data['main']['temp_max'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'city': city_exists(data['name']).id,
            'datetime': datetime.now(tz=local_timezone),
        }
        return weather_data

    except requests.exceptions.HTTPError as err:
        # city not found
        if err.response.status_code == 404:
            raise Exception("City not found")

        # bad request
        elif err.response.status_code == 400:
            raise Exception("Bad Request")

        # when an authenticated request fails the permission checks
        elif err.response.status_code == 403:
            raise Exception("Forbidden, fails the permission checks")

        # when an incoming request occurs that does not map to a handler method on the view.
        elif err.response.status_code == 405:
            raise Exception("Method Not Allowed")

        # service_unavailable
        elif err.response.status_code == 503:
            raise Exception('Service temporarily unavailable, try again later.')

        else:
            # other HTTP errors
            raise Exception('Error fetching weather data')


# to know the weather for any user
class WeatherView(APIView):
    def get(self, request, city_name):
        # get weather from function
        weather_data = get_weather(city_name)

        serializer = WeatherViewSerializer(data=weather_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Register
class RegisterApi(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User Created Successfully.",
        }, status=status.HTTP_201_CREATED)


class Subscriptions(APIView):
    # possible only for authenticated users
    permission_classes = [IsAuthenticated]

    @retry(exceptions=(Exception, IntegrityError, OperationalError), tries=3, delay=1, backoff=2)
    def save_subscription(self, user, city_name, period_of_notification):
        try:
            subscription = Subscription.objects.create(
                user=user,
                city=city_exists(city_name),
                period_of_notification=period_of_notification,
                updated_at=datetime.now(tz=local_timezone),
            )
            subscription.save()
            return subscription
        except IntegrityError:
            raise Exception("Error saving subscription to the database")
        except OperationalError:
            raise Exception(
                "Database operation fails due to a temporary issue, such as a connection error or a timeout.")

    @retry(exceptions=(Exception, IntegrityError, OperationalError), tries=3, delay=1, backoff=2)
    def update_subscription(self, user, city_name, period_of_notification):
        try:
            # search subscription by user_id and city_name
            subscription = Subscription.objects.get(user=user, city=city_exists(city_name).id)

            # change data to new
            subscription.period_of_notification = period_of_notification
            subscription.updated_at = datetime.now(tz=local_timezone)
            subscription.save()
            return subscription
        except IntegrityError:
            raise Exception("Error updating subscription in the database")
        except OperationalError:
            raise Exception(
                "Database operation fails due to a temporary issue, such as a connection error or a timeout.")

    @retry(exceptions=(Exception, IntegrityError, OperationalError), tries=3, delay=1, backoff=2)
    def delete_subscription(self, user, city_name):
        try:
            # search subscription by user_id and city_name
            subscription = Subscription.objects.get(user=user, city=City.objects.get(city_name=city_name).id)
            subscription.delete()
        except IntegrityError:
            raise Exception("Error deleting subscription from the database")
        except OperationalError:
            raise Exception(
                "Database operation fails due to a temporary issue, such as a connection error or a timeout.")

    # get all subscriptions
    def get(self, request):
        user = request.user.id
        query = Subscription.objects.filter(user=user)
        serializer = SubscriptionsSerializer(query, many=True)
        return Response(serializer.data)

    # create a new subscription
    def post(self, request, city_name, period_of_notification):
        user = request.user
        subsription = self.save_subscription(user, city_exists(city_name), period_of_notification)
        serializer = SubscriptionsSerializer(subsription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # update a subscription
    def put(self, request, city_name, period_of_notification):
        user = request.user.id

        # search subscription by user_id and city_name
        subsription = self.update_subscription(user, city_name, period_of_notification)
        serializer = SubscriptionsSerializer(subsription)
        return Response(serializer.data, status.HTTP_200_OK)

    # delete a subscription
    def delete(self, request, city_name):
        user = request.user.id
        self.delete_subscription(user, city_name)
        return Response("Subscription has been deleted", status.HTTP_200_OK)
