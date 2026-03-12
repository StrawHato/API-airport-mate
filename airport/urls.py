from django.urls import path, include

from rest_framework import routers

from airport.views import (
    AirplaneTypeViewSet,
    AirplaneViewSet,
    CrewViewSet,
    AirportViewSet,
    RouteViewSet
)

router = routers.DefaultRouter()
router.register(
    "airplane-types",
    AirplaneTypeViewSet,
    basename="airplane-type",
)
router.register("airplanes", AirplaneViewSet, basename="airplane")
router.register("crew", CrewViewSet, basename="crew")
router.register("airports", AirportViewSet, basename="airport")
router.register("routes", RouteViewSet, basename="route")

urlpatterns = [path("", include(router.urls))]

app_name = "airport"
