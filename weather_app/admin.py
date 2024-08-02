from django.contrib import admin
from .models import Subscription, Weather, City

admin.site.register([Subscription, Weather, City])