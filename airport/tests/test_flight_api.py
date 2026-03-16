from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import (
    AirplaneType,
    Airplane,
    Airport,
    Country,
    Route,
    Flight,
    Crew,
)


FLIGHT_URL = reverse("airport:flight-list")


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


def sample_airplane(airplane_type):

    return Airplane.objects.create(
        name="Boeing 737",
        rows=20,
        seats_in_row=6,
        airplane_type=airplane_type,
    )


def sample_airport(name):
    country = Country.objects.create(name="Ukraine")

    return Airport.objects.create(
        name=name,
        closest_big_city="City",
        country=country,
    )


def sample_route(source_name="Boryspil", destination_name="Paris"):
    source = sample_airport(source_name)
    destination = sample_airport(destination_name)

    return Route.objects.create(
        source=source,
        destination=destination,
        distance=1000,
    )


def sample_flight(**params):
    airplane_type = AirplaneType.objects.get_or_create(name="Boeing")[0]
    airplane = sample_airplane(airplane_type)
    route = sample_route()

    crew = Crew.objects.create(
        first_name="John",
        last_name="Doe",
    )

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": timezone.now(),
        "arrival_time": timezone.now() + timedelta(hours=2),
    }

    defaults.update(params)

    flight = Flight.objects.create(**defaults)
    flight.crew.add(crew)

    return flight


class UnauthenticatedFlightTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test authentication is required"""
        res = self.client.get(FLIGHT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpass123",
        )

        self.client.force_authenticate(self.user)

    def test_flight_list(self):
        """Test retrieving flight list"""
        sample_flight()
        sample_flight()

        res = self.client.get(FLIGHT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_flight_detail(self):
        """Test retrieving flight detail"""
        flight = sample_flight()

        url = detail_url(flight.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], flight.id)

    def test_filter_by_source(self):
        """Test filtering flights by source airport"""
        route1 = sample_route("Boryspil", "Paris")
        route2 = sample_route("Kyiv", "London")

        flight1 = sample_flight(route=route1)
        sample_flight(route=route2)

        res = self.client.get(FLIGHT_URL, {"source": "Boryspil"})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], flight1.id)

    def test_filter_by_destination(self):
        """Test filtering flights by destination airport"""
        route1 = sample_route("Kyiv", "Paris")
        route2 = sample_route("Kyiv", "London")

        flight1 = sample_flight(route=route1)
        sample_flight(route=route2)

        res = self.client.get(FLIGHT_URL, {"destination": "Paris"})

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], flight1.id)

    def test_filter_by_departure_date(self):
        """Test filtering flights by departure date"""
        today = timezone.now()

        flight1 = sample_flight(departure_time=today)
        sample_flight(departure_time=today + timedelta(days=1))

        res = self.client.get(
            FLIGHT_URL,
            {"departure": today.date().isoformat()}
        )

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["id"], flight1.id)

    def test_create_flight_forbidden(self):
        """Test normal user cannot create flight"""
        route = sample_route()
        airplane_type = AirplaneType.objects.get_or_create(name="Boeing")[0]
        airplane = sample_airplane(airplane_type)
        crew = Crew.objects.create(
            first_name="John",
            last_name="Doe",
        )

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "crew": [crew.id],
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timedelta(hours=2),
        }

        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpass123",
        )
        self.client.force_authenticate(self.admin)

    def test_create_flight(self):
        """Test admin can create flight"""
        route = sample_route()
        airplane_type = AirplaneType.objects.get_or_create(name="Boeing")[0]
        airplane = sample_airplane(airplane_type)
        crew = Crew.objects.create(
            first_name="John",
            last_name="Doe",
        )

        payload = {
            "route": route.id,
            "airplane": airplane.id,
            "crew": [crew.id],
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timedelta(hours=2),
        }

        res = self.client.post(FLIGHT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Flight.objects.count(), 1)
