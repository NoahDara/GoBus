from django.db import models
from helpers.models import BaseModel
from drivers.models import Driver


class Bus(BaseModel):
    """
    Represents a physical bus in the fleet.
    A driver can be assigned and changed at any time.
    Seats are auto-generated via signal when a bus is created.
    """
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='buses'
    )
    bus_number = models.CharField(max_length=20, unique=True)
    plate_number = models.CharField(max_length=20, unique=True)
    capacity = models.PositiveIntegerField()
    is_operational = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.bus_number} - {self.plate_number}"

    class Meta:
        verbose_name_plural = "Buses"


class Seat(BaseModel):
    """
    Represents a physical seat on a bus.
    Row 1 has 3 seats, all subsequent rows have 5 seats.
    Auto-generated via signal when a Bus is created.
    Availability is checked dynamically at booking time — no is_available field.
    """
    bus = models.ForeignKey(
        Bus,
        on_delete=models.CASCADE,
        related_name='seats'
    )
    seat_number = models.PositiveIntegerField()
    row = models.PositiveIntegerField()

    def __str__(self):
        return f"Bus {self.bus.bus_number} - Row {self.row} Seat {self.seat_number}"

    class Meta:
        unique_together = ['bus', 'seat_number']
        ordering = ['row', 'seat_number']


class Route(BaseModel):
    """
    Represents a named route from origin to destination.
    When a route is created, a reverse route is auto-created via signal.
    Reverse routes are linked via reverse_of and is_reverse flag.
    Pricing lives entirely in RouteSegment — no fare fields here.
    """
    name = models.CharField(max_length=100)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    estimated_duration = models.DurationField(
        null=True,
        blank=True,
        help_text="Estimated travel time e.g. 01:30:00"
    )
    is_reverse = models.BooleanField(
        default=False,
        help_text="True if this route was auto-generated as a reverse"
    )
    reverse_of = models.OneToOneField(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reverse_route'
    )

    def calculate_fare(self, boarding_stop_order, alighting_stop_order):
        """
        Sums segment prices between boarding and alighting stops.
        e.g. boarding=1 (Harare), alighting=3 (Chivhu) = $2 + $3 = $5
        Uses from_stop__order < alighting to avoid double-counting
        the final stop.
        """
        segments = self.segments.filter(
            from_stop__order__gte=boarding_stop_order,
            to_stop__order__lte=alighting_stop_order
        ).order_by('from_stop__order')
        return sum(s.price for s in segments)

    def __str__(self):
        return f"{self.origin} → {self.destination}"


class RouteStop(BaseModel):
    """
    Represents a single stop along a route.
    Order determines the sequence of stops on the route.
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='stops'
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(
        help_text="Position in route e.g. 1=origin, last=destination"
    )

    def __str__(self):
        return f"{self.route.name} - Stop {self.order}: {self.name}"

    class Meta:
        ordering = ['route', 'order']
        unique_together = ['route', 'order']


class RouteSegment(BaseModel):
    """
    Defines the fixed admin-set price between two consecutive stops.
    e.g. Harare (stop 1) → Beatrice (stop 2) = $2
         Beatrice (stop 2) → Chivhu (stop 3) = $3
    Reverse segments are auto-created with the same price when
    the reverse route is generated.
    """
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='segments'
    )
    from_stop = models.ForeignKey(
        RouteStop,
        on_delete=models.CASCADE,
        related_name='segments_from'
    )
    to_stop = models.ForeignKey(
        RouteStop,
        on_delete=models.CASCADE,
        related_name='segments_to'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.from_stop.name} → {self.to_stop.name}: ${self.price}"

    class Meta:
        unique_together = ['route', 'from_stop', 'to_stop']


class Schedule(BaseModel):
    """
    Represents a specific trip — a bus running a route on a given date/time.
    available_seats is auto-set from bus capacity on creation
    and decremented as bookings are confirmed.
    """
    bus = models.ForeignKey(
        Bus,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='scheduled'
    )
    available_seats = models.PositiveIntegerField(editable=False)

    def __str__(self):
        return (
            f"{self.bus.bus_number} | {self.route.name} | "
            f"{self.departure_time.strftime('%Y-%m-%d %H:%M')}"
        )

    class Meta:
        ordering = ['departure_time']