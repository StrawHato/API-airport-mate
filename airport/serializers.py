from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from airport.models import (
    AirplaneType,
    Airplane,
    Crew,
    Airport,
    Route,
    Flight,
    Ticket,
    Order,
    Country,
)


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = serializers.CharField(
        source="airplane_type.name",
        read_only=True,
    )

    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity"
        )


class AirplaneCompressedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = ("name", "rows", "seats_in_row", "capacity")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name")


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city", "country", "image")


class AirportListRetrieveSerializer(AirportSerializer):
    country = serializers.CharField(source="country.name", read_only=True)


class ImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "image",)


class RouteSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if attrs["source"] == attrs["destination"]:
            raise ValidationError(
                "Source and destination cannot be the same airport"
            )
        return attrs

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.CharField(
        source="source.name",
        read_only=False,
    )
    destination = serializers.CharField(
        source="destination.name",
        read_only=False,
    )


class RouteDetailSerializer(RouteSerializer):
    source = AirportListRetrieveSerializer(many=False, read_only=True)
    destination = AirportListRetrieveSerializer(many=False, read_only=True)


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id","route", "airplane", "crew", "departure_time", "arrival_time")


class FlightListSerializer(FlightSerializer):
    route = RouteListSerializer(many=False, read_only=True)
    airplane = AirplaneCompressedSerializer(many=False, read_only=True)
    crew = serializers.SlugRelatedField(
        read_only=True,
        many=True,
        slug_field="full_name",
    )


class FlightDetailSerializer(FlightSerializer):
    route = RouteDetailSerializer(many=False, read_only=True)
    airplane = AirplaneSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["flight"].airplane,
            ValidationError
        )
        return data


class TicketListSerializer(TicketSerializer):
    flight = FlightListSerializer(many=False, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket in tickets_data:
                Ticket.objects.create(order=order, **ticket)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=False, allow_empty=False)
