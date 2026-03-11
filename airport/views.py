from rest_framework import viewsets

from airport.models import AirplaneType
from airport.serializers import AirplaneTypeSerializer


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
