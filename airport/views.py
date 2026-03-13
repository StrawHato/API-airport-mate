from datetime import datetime

from django.db.models import Count, F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, pagination, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from airport.permissions import IsAdminOrIfAuthenticatedReadOnly
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
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="name",
                type=OpenApiTypes.STR,
                description="Filter by airplane name (e.g. ?name=Boeing 737).",
                required=False,
            ),
            OpenApiParameter(
                name="airplane_type",
                type=OpenApiTypes.STR,
                description="Filter by airplane_type name (e.g. ?type=Airbus).",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Retrieve a list of airplanes with optional filtering."""
        return super().list(request, *args, **kwargs)


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirportViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.prefetch_related("country")
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="country",
                type=OpenApiTypes.STR,
                description="Filter by airport country name (e.g. ?country=Ukraine).",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Retrieve a list of airports with optional filtering."""
        return super().list(request, *args, **kwargs)


class RoutePagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 10


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    pagination_class = RoutePagination

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
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        elif self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer

    def get_queryset(self):
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        departure = self.request.query_params.get("departure")

        if source:
            return self.queryset.filter(
                route__source__name__icontains=source
            )
        if destination:
            return self.queryset.filter(
                route__destination__name__icontains=destination
            )
        if departure:
            date = datetime.strptime(departure, "%Y-%m-%d").date()
            return self.queryset.filter(
                departure_time__date=date
            )
        return self.queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="source",
                type=OpenApiTypes.STR,
                description="Filter by source airport name (e.g. ?source=Boryspil).",
                required=False,
            ),
            OpenApiParameter(
                name="destination",
                type=OpenApiTypes.STR,
                description="Filter by destination airport name (e.g. ?destination=Charles de Gaulle Airport).",
                required=False,
            ),
            OpenApiParameter(
                name="departure",
                type=OpenApiTypes.DATE,
                description="Filter by departure time (e.g. ?departure=2026-04-01).",
                required=False,
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """Retrieve a list of flights with optional filtering."""
        return super().list(request, *args, **kwargs)


class OrderPagination(pagination.PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer
        return OrderSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
