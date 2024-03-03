from rest_framework import generics, status
from myapp.models import Car
from myapp.api.serializers import CarSerializer, CarFullSerializer
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import AllowAny
from rest_framework import viewsets


class CarEnrollView(APIView):
    # authentication_classes = [BasicAuthentication]  # https://www.django-rest-framework.org/api-guide/authentication/
    # permission_classes = AllowAny  # https://www.django-rest-framework.org/api-guide/permissions/
    def post(self, request, name, color, max_speed):
        if max_speed > 10 and max_speed < 300:
            Car.objects.create(name=name, color=color, max_speed=max_speed)
            return Response({'enrolled': True})
        else:
            return Response({'error': 'Max speed should be between 10 and 300'}, status=status.HTTP_400_BAD_REQUEST)


class CarViewsSet(viewsets.ReadOnlyModelViewSet):
    queryset = Car.objects.all()
    serializer_class = CarFullSerializer


class CarListViews(generics.ListAPIView):
    queryset = Car.objects.all()
    serializer_class = CarSerializer


class CarDetailView(generics.RetrieveAPIView):
    queryset = Car.objects.all()
    serializer_class = CarSerializer
