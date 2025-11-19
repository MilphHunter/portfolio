from django.db import models

class Categories(models.Model):
    name = models.CharField()
    url = models.URLField(max_length=255, unique=True)

    status = models.CharField(max_length=6, default='New')

class Event(models.Model):
    event_id = models.CharField()
    name = models.CharField(blank=True, null=True)
    location = models.CharField(blank=True, null=True)
    date = models.CharField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    status = models.CharField(default='New', max_length=9)

class Ticket(models.Model):
    event = models.CharField()

    ticket_id = models.CharField(null=True, blank=True)
    section = models.CharField(null=True, blank=True)
    row = models.CharField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    note = models.CharField(null=True, blank=True)
    is_eticket = models.BooleanField(default=False)
    is_instant_delivery = models.BooleanField(default=False)
    event_date = models.DateTimeField(null=True, blank=True)
    delivery_text = models.CharField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_agent_only = models.BooleanField(default=False)
    quality = models.FloatField(null=True, blank=True)
    is_best_deal = models.BooleanField(default=False)
    is_low_price = models.BooleanField(default=False)
    is_money_saver = models.BooleanField(default=False)
    deal_value = models.FloatField(null=True, blank=True)
    face_value = models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)