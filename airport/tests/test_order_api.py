from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import (
    Crew,
    Airplane,
    AirplaneType,
    Country,
    Airport,
    Route, Ticket, Order, Flight
)

ORDER_URL = reverse("airport:order-list")


def sample_airplane(**kwargs):
    airplane_type = AirplaneType.objects.create(
        name="Boeing"
    )

    defaults = {
        "name": "Boeing 650",
        "rows": 20,
        "seats_in_row": 6,
        "airplane_type": airplane_type
    }
    defaults.update(kwargs)
    return Airplane.objects.create(**defaults)


def sample_airport(**kwargs):
    country = Country.objects.create(
        name="Ukraine"
    )
    defaults = {
        "name": "Boryspil International Airport",
        "closest_big_city": "Kyiv",
        "country": country,
        "image": None
    }
    defaults.update(kwargs)
    return Airport.objects.create(**defaults)


def sample_flight(**kwargs):
    crew = Crew.objects.create(
        first_name="John",
        last_name="Doe",
    )

    airport1 = sample_airport()
    airport2 = sample_airport(name="Kharkiv International Airport")
    airplane = sample_airplane()
    route = Route.objects.create(
        source=airport1,
        destination=airport2,
        distance=650,
    )

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": timezone.now(),
        "arrival_time": timezone.now() + timedelta(hours=3),
    }
    defaults.update(kwargs)

    flight = Flight.objects.create(**defaults)
    flight.crew.add(crew)

    return flight


def sample_ticket_payload(row, seat, flight_id):
    return {
        "row": row,
        "seat": seat,
        "flight": flight_id,
    }


class UnauthenticatedOrderTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedUserOrderTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpass123",
        )

        self.client.force_authenticate(self.user)

    def test_order_list(self):
        """User can retrieve their orders"""

        flight = sample_flight()

        order = Order.objects.create(user=self.user)

        Ticket.objects.create(
            row=1,
            seat=1,
            flight=flight,
            order=order,
        )

        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)

    def test_order_list_limited_to_user(self):
        """User sees only their orders"""

        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="pass123",
        )

        flight = sample_flight()

        Order.objects.create(user=other_user)

        order = Order.objects.create(user=self.user)

        Ticket.objects.create(
            row=1,
            seat=1,
            flight=flight,
            order=order,
        )

        res = self.client.get(ORDER_URL)

        self.assertEqual(len(res.data["results"]), 1)

    def test_create_order_forbidden(self):
        """Normal user cannot create orders"""

        flight = sample_flight()

        payload = {
            "tickets": [
                sample_ticket_payload(1, 1, flight.id)
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminOrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpass",
        )

        self.client.force_authenticate(self.admin)

    def test_create_order(self):
        """Admin can create order with ticket"""

        flight = sample_flight()

        payload = {
            "tickets": [
                sample_ticket_payload(1, 1, flight.id)
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_create_order_multiple_tickets(self):
        """Admin can create multiple tickets"""

        flight = sample_flight()

        payload = {
            "tickets": [
                sample_ticket_payload(1, 2, flight.id),
                sample_ticket_payload(1, 3, flight.id),
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Ticket.objects.count(), 2)

    def test_create_ticket_invalid_row(self):
        """Row validation"""

        flight = sample_flight()

        payload = {
            "tickets": [
                sample_ticket_payload(row=100, seat=1, flight_id=flight.id)
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ticket_invalid_seat(self):
        """Seat validation"""

        flight = sample_flight()

        payload = {
            "tickets": [
                sample_ticket_payload(flight_id=flight.id, row=1, seat=100)
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_ticket_taken_seat(self):
        """Cannot book taken seat"""

        flight = sample_flight()

        order = Order.objects.create(user=self.admin)

        Ticket.objects.create(
            row=1,
            seat=1,
            flight=flight,
            order=order,
        )

        payload = {
            "tickets": [
                sample_ticket_payload(1, 1, flight.id)
            ]
        }

        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
