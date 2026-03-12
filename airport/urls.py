from django.urls import path, include

from rest_framework import routers

from airport.views import (
    AirplaneTypeViewSet,
    AirplaneViewSet,
    CrewViewSet
)

router = routers.DefaultRouter()
router.register(
    "airplane-type",
    AirplaneTypeViewSet,
    basename="airplane-type",
)
router.register("airplane", AirplaneViewSet, basename="airplane")
router.register("crew", CrewViewSet, basename="crew")

urlpatterns = [path("", include(router.urls))]

app_name = "airport"
