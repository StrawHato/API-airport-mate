from rest_framework import viewsets

from airport.models import (
    AirplaneType,
    Airplane,
    Crew
)

from airport.serializers import (
    AirplaneTypeSerializer,
    AirplaneSerializer,
    CrewSerializer
)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
