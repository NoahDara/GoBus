from .models import Seat, Route, RouteStop, RouteSegment


def generate_seats_for_bus(bus):
    """
    Generates Seat records for a given Bus instance.
    Layout:
        Row 1  → 3 seats (front row)
        Row 2+ → 5 seats each
    Uses bulk_create for efficiency.
    """
    seats = []
    seat_number = 1
    row = 1
    remaining = bus.capacity

    # Row 1 — 3 seats
    first_row_count = min(3, remaining)
    for _ in range(first_row_count):
        seats.append(Seat(bus=bus, seat_number=seat_number, row=row))
        seat_number += 1
    remaining -= first_row_count
    row += 1

    # Rows 2 onwards — 5 seats each
    while remaining > 0:
        seats_in_row = min(5, remaining)
        for _ in range(seats_in_row):
            seats.append(Seat(bus=bus, seat_number=seat_number, row=row))
            seat_number += 1
        remaining -= seats_in_row
        row += 1

    Seat.objects.bulk_create(seats)


def create_reverse_route(route):
    """
    Creates a reverse route from an existing route.
    e.g. Mutare → Masvingo becomes Masvingo → Mutare.

    Steps:
        1. Create the reverse Route record
        2. Re-create stops in reversed order
        3. Flip each segment (from↔to) with the same price
        4. Link reverse_of back to the original route

    Skips creation if a reverse already exists to prevent duplicates.
    """
    # Guard — never reverse a reverse, never duplicate
    if route.is_reverse:
        return

    if hasattr(route, 'reverse_route') and route.reverse_route is not None:
        return

    # 1. Create reverse route
    reverse = Route.objects.create(
        name=f"{route.destination} - {route.origin}",
        origin=route.destination,
        destination=route.origin,
        estimated_duration=route.estimated_duration,
        is_reverse=True,
        reverse_of=route,
    )

    # 2. Create reversed stops — original last stop becomes stop 1
    original_stops = list(route.stops.order_by('order'))
    stop_map = {}  # original stop uid → new reversed RouteStop

    for i, original_stop in enumerate(reversed(original_stops)):
        new_stop = RouteStop.objects.create(
            route=reverse,
            name=original_stop.name,
            order=i + 1,
        )
        stop_map[original_stop.uid] = new_stop

    # 3. Flip each segment — same price, from↔to swapped
    for segment in route.segments.select_related('from_stop', 'to_stop'):
        RouteSegment.objects.create(
            route=reverse,
            from_stop=stop_map[segment.to_stop.uid],
            to_stop=stop_map[segment.from_stop.uid],
            price=segment.price,
        )

    return reverse


def sync_reverse_route(route):
    """
    Syncs the reverse route when the original route is updated.
    Updates name, duration on the reverse route.
    Called manually from the view or admin when a route is edited.
    Does not re-create stops or segments — those require
    deleting and recreating the reverse route entirely.
    """
    if route.is_reverse:
        return

    try:
        reverse = route.reverse_route
    except Route.DoesNotExist:
        create_reverse_route(route)
        return

    reverse.name = f"{route.destination} - {route.origin}"
    reverse.origin = route.destination
    reverse.destination = route.origin
    reverse.estimated_duration = route.estimated_duration
    reverse.save()
    
    
def sync_reverse_route_stops(forward_route):
    """
    Sync route stops from forward route to reverse route.
    When forward route stops change, reverse route stops are updated to match (in reverse order).
    """
    from .models import RouteStop, RouteSegment
    
    if not forward_route or forward_route.is_reverse:
        return
    
    reverse_route = forward_route.reverse_route
    if not reverse_route:
        return
    
    # Get forward stops in order
    forward_stops = list(forward_route.stops.order_by('order'))
    
    if not forward_stops:
        # Delete all reverse stops if no forward stops
        reverse_route.stops.all().delete()
        return
    
    # Delete all reverse stops and recreate in reverse order
    reverse_route.stops.all().delete()
    
    # Create reverse stops (reversed order)
    reverse_stops_map = {}
    for index, fwd_stop in enumerate(reversed(forward_stops), 1):
        rev_stop = RouteStop.objects.create(
            route=reverse_route,
            name=fwd_stop.name,
            order=index
        )
        reverse_stops_map[fwd_stop.uid] = rev_stop
    
    # Sync segments (if any exist)
    forward_segments = list(forward_route.segments.select_related('from_stop', 'to_stop').order_by('from_stop__order'))
    
    if forward_segments:
        # Delete reverse segments
        reverse_route.segments.all().delete()
        
        # Create reverse segments (in reverse order)
        for segment in reversed(forward_segments):
            RouteSegment.objects.create(
                route=reverse_route,
                from_stop=reverse_stops_map[segment.to_stop.uid],
                to_stop=reverse_stops_map[segment.from_stop.uid],
                price=segment.price
            )