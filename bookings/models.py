from django.db import models
from django.contrib.auth.models import User
from helpers.models import BaseModel
from buses.models import Schedule, Seat, RouteStop


class Booking(BaseModel):
    """
    Represents a passenger's seat reservation on a specific schedule.

    Fare is calculated at booking time using Route.calculate_fare()
    based on the boarding and alighting stops.

    A seat is considered available for a given schedule if no confirmed
    booking exists on that seat where the stop ranges overlap.
    Overlap check is handled in bookings/helpers.py.
    """
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    boarding_stop = models.ForeignKey(
        RouteStop,
        on_delete=models.CASCADE,
        related_name='boardings'
    )
    alighting_stop = models.ForeignKey(
        RouteStop,
        on_delete=models.CASCADE,
        related_name='alightings'
    )
    fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Fare calculated at time of booking"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    booking_reference = models.CharField(
        max_length=12,
        unique=True,
        editable=False
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.booking_reference} | {self.user.get_full_name()} | {self.schedule}"

    class Meta:
        ordering = ['-created']