from django.db import models
from django.contrib.auth.models import User

class MarathonEvent(models.Model):
    DISTANCE_CHOICES = [
        ('5K', '5 Kilometers'),
        ('10K', '10 Kilometers'),
        ('21K', '21 Kilometers'),
        ('42K', '42 Kilometers'),
        ('ULTRA', 'Ultra Marathon'),
    ]

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    event_date = models.DateTimeField()
    flag_off_time = models.TimeField()
    cut_off_time = models.TimeField()
    distance = models.CharField(max_length=10, choices=DISTANCE_CHOICES)
    max_participants = models.IntegerField()
    current_participants = models.IntegerField(default=0)
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='upcoming')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Route information
    start_point = models.CharField(max_length=200)
    finish_point = models.CharField(max_length=200)
    route_description = models.TextField(blank=True)
    water_stations = models.TextField(blank=True)  # JSON or comma-separated

    def __str__(self):
        return self.name

    @property
    def is_registration_open(self):
        return self.status == 'upcoming' and self.current_participants < self.max_participants

class EventRegistration(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    REGISTRATION_STATUS_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(MarathonEvent, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)
    bib_number = models.CharField(max_length=10, blank=True, null=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    registration_status = models.CharField(max_length=10, choices=REGISTRATION_STATUS_CHOICES, default='pending')
    payment_proof = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)
    finish_time = models.TimeField(blank=True, null=True)

    class Meta:
        unique_together = ['user', 'event']

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"
