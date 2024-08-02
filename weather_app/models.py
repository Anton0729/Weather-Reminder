from django.contrib.auth.models import User
from django.db import models


class City(models.Model):
    city_name = models.CharField(max_length=100)

    def __str__(self):
        return self.city_name


class Subscription(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    period_of_notification = models.IntegerField(default=12, help_text='Period of notification in hours')
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.period_of_notification}"


class Weather(models.Model):
    description = models.CharField(max_length=200, help_text='Weather condition')
    temperature = models.FloatField(help_text='Temperature in Celsius')
    temperature_min = models.FloatField(help_text='Minimum temperature in Celsius')
    temperature_max = models.FloatField(help_text='Maximum temperature in Celsius')
    humidity = models.FloatField(help_text='Humidity, %')
    wind_speed = models.FloatField(help_text='Wind speed in metre/sec')
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    datetime = models.DateTimeField()
