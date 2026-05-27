import random
import string
from .models import Booking


def generate_booking_reference(booking):
    """
    Generates a unique 10-character booking reference.
    Format: GB-XXXXXXXX (GB for GoBus + 8 alphanumeric chars)
    Retries until unique.
    """
    while True:
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        ref = f"GB-{suffix}"
        if not Booking.objects.filter(booking_reference=ref).exists():
            return ref


def get_available_seats(schedule, boarding_stop, alighting_stop):
    """
    Returns a queryset of Seat objects that are available for a given
    schedule between the boarding and alighting stops.

    A seat is UNAVAILABLE if a confirmed booking exists on that seat
    where the booked stop range overlaps with the requested range.

    Overlap condition:
        existing.boarding_stop.order < alighting_stop.order
        AND
        existing.alighting_stop.order > boarding_stop.order

    This correctly handles all overlap cases:
        - Harare→Beatrice blocks Harare→Beatrice (same range)
        - Harare→Chivhu blocks Harare→Beatrice (superset)
        - Harare→Chivhu blocks Beatrice→Chivhu (subset)
        - Harare→Beatrice does NOT block Beatrice→Masvingo (adjacent, no overlap)
    """
    booked_seat_ids = Booking.objects.filter(
        schedule=schedule,
        status=Booking.STATUS_CONFIRMED,
        boarding_stop__order__lt=alighting_stop.order,
        alighting_stop__order__gt=boarding_stop.order,
    ).values_list('seat_id', flat=True)

    return schedule.bus.seats.exclude(uid__in=booked_seat_ids)


def calculate_booking_fare(schedule, boarding_stop, alighting_stop):
    """
    Calculates the fare for a booking using the route's segment pricing.
    Delegates to Route.calculate_fare().
    """
    return schedule.route.calculate_fare(
        boarding_stop.order,
        alighting_stop.order
    )