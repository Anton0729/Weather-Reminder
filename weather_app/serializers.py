from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Subscription, Weather


# creating a serializer
class WeatherViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Weather
        fields = ('description', 'temperature', 'temperature_min', 'temperature_max', 'humidity', 'wind_speed', 'city', 'datetime')


# Register serializer
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'password': {'required': True},
        }

    def validate_username(self, username):
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("This username is already taken!")
        return username

    def validate_email(self, email):
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError("This email is already taken!")
        return email

    def validate_password(self, password):
        validate_password(password)
        return password

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], email=validated_data['email'],
                                        password=validated_data['password'])
        return user


# User serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class SubscriptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = '__all__'
