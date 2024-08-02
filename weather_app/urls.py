from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from weather_app.views import WeatherView, RegisterApi, Subscriptions

app_name = 'DjangoWeatherReminder'

urlpatterns = [
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/drf-auth/', include('rest_framework.urls')),
    path('api/v1/register/', RegisterApi.as_view(), name='register'),
    path('api/v1/weather/<str:city_name>/', WeatherView.as_view(), name='city_weather'),
    path('api/v1/subscriptions/', Subscriptions.as_view(), name='subscriptions'),
    path('api/v1/subscriptions/<str:city_name>/<str:period_of_notification>', Subscriptions.as_view(), name='update_subscription'),
    path('api/v1/subscriptions/<str:city_name>/', Subscriptions.as_view(), name='delete_subscription'),
]
