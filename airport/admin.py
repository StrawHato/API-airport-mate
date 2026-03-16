from django.contrib import admin

from airport.models import (
    AirplaneType,
    Airplane,
    Airport,
    Crew,
    Route,
    Flight,
    Ticket,
    Order
)


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [TicketInline]


admin.site.register(AirplaneType)
admin.site.register(Airplane)
admin.site.register(Airport)
admin.site.register(Crew)
admin.site.register(Route)
admin.site.register(Flight)
