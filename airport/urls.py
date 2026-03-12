from django.urls import path, include

from rest_framework import routers

from airport.views import (
    AirplaneTypeViewSet,
    AirplaneViewSet
)

router = routers.DefaultRouter()
router.register(
    "airplane-type",
    AirplaneTypeViewSet,
    basename="airplane-type",
)
router.register("airplane", AirplaneViewSet, basename="airplane")

urlpatterns = [path("", include(router.urls))]

app_name = "airport"
