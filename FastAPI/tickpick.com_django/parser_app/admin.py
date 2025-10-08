from django.contrib import admin
from .models import Event, Ticket

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "status")

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("event", "section", "row", "price", "face_value")