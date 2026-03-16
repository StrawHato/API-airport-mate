import tempfile

from PIL import Image

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status

from airport.models import Airport, Country
from airport.serializers import AirportListRetrieveSerializer

AIRPORT_URL = reverse("airport:airport-list")


def detail_url(airport_id):
    return reverse("airport:airport-detail", args=[airport_id])


def image_upload_url(airport_id):
    return reverse("airport:airport-upload-image", args=[airport_id])


def sample_country(name="Ukraine"):
    country, _ = Country.objects.get_or_create(name=name)
    return country


def sample_airport(**params):
    country = Country.objects.get(id=1)
    defaults = {
        "name": "Boryspil International Airport",
        "closest_big_city": "Kyiv",
        "country": country,
    }
    defaults.update(params)
    return Airport.objects.create(**defaults)


class UnauthenticatedAirportTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(AIRPORT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAirportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)
        sample_country()

    def test_airport_list(self):
        sample_airport()
        sample_airport(name="Kharkiv Airport")

        res = self.client.get(AIRPORT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_airport_detail(self):
        airport = sample_airport()

        res = self.client.get(detail_url(airport.id))
        serializer = AirportListRetrieveSerializer(airport)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filter_by_country(self):
        country1 = sample_country("Ukraine")
        country2 = sample_country("France")

        airport1 = sample_airport(country=country1)
        sample_airport(country=country2)

        res = self.client.get(AIRPORT_URL, {"country": "Ukraine"})
        serializer = AirportListRetrieveSerializer(airport1)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0], serializer.data)

    def test_create_airport_forbidden(self):
        country = Country.objects.get(id=1)
        payload = {
            "name": "New Airport",
            "closest_big_city": "City",
            "country": country.id,
        }
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAirportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpass",
        )
        self.client.force_authenticate(self.admin)
        sample_country()

    def test_create_airport(self):
        country = Country.objects.get(id=1)
        payload = {
            "name": "New Airport",
            "closest_big_city": "City",
            "country": country.id,
        }
        res = self.client.post(AIRPORT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airport.objects.count(), 1)

    def test_upload_image(self):
        airport = sample_airport()
        url = image_upload_url(airport.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)

            res = self.client.post(
                url,
                {"image": ntf},
                format="multipart"
            )

        airport.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(airport.image)

    def test_upload_invalid_image(self):
        airport = sample_airport()
        url = image_upload_url(airport.id)
        res = self.client.post(
            url,
            {"image": "not-image"},
            format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
