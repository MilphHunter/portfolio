from rest_framework import serializers
from myapp.models import Car


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['id', 'name']


class CarFullSerializer(serializers.ModelSerializer):
    color = serializers.CharField(source='get_color_display')

    class Meta:
        model = Car
        fields = ['id', 'name', 'color']
