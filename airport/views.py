from django.db.models import Count, F
from rest_framework import viewsets, pagination, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from airport.models import (
    AirplaneType,
    Airplane,
    Crew,
    Airport,
    Route,
    Flight,
    Order, Country
)

from airport.serializers import (
    AirplaneTypeSerializer,
    AirplaneSerializer,
    AirplaneListDetailSerializer,
    CrewSerializer,
    AirportSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    FlightSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
    ImageUploadSerializer,
    AirportListRetrieveSerializer,
    CountrySerializer,
)


class AirplaneTypeViewSet(viewsets.ModelViewSet):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer
    pagination_class = None


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirplaneListDetailSerializer
        return AirplaneSerializer

    def get_queryset(self):
        name = self.request.query_params.get("name")
        airplane_type = self.request.query_params.get("airplane_type")
        if name:
            return self.queryset.filter(
                name__icontains=name
            )
        if airplane_type:
            return self.queryset.filter(
                airplane_type__name__icontains=airplane_type
            )
        return self.queryset


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    pagination_class = None


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    pagination_class = None


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.prefetch_related("country")
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirportListRetrieveSerializer
        elif self.action == "upload_image":
            return ImageUploadSerializer
        return AirportSerializer

    def get_queryset(self):
        country = self.request.query_params.get("country")

        if country:
            return Airport.objects.filter(country__name__icontains=country)
        return self.queryset

    @action(
        detail=True,
        methods=["POST"],
        url_path="upload-image",
        permission_classes=(IsAdminUser,),
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific airport"""
        airport = self.get_object()
        serializer = self.get_serializer(airport, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        elif self.action == "retrieve":
            return RouteDetailSerializer
        return RouteSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight.objects
        .select_related(
            "route",
            "route__source",
            "route__destination",
            "route__source__country",
            "route__destination__country",
            "airplane",
            "airplane__airplane_type",
        )
        .prefetch_related(
            "crew",
            "tickets",
        )
        .annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row")
                    - Count("tickets")
            )
        )
    )
    serializer_class = FlightSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer


class OrderPagination(pagination.PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
