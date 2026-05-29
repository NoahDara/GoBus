# buses/signals.py - Updated with auto-create stops

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Bus, Route, Schedule, RouteStop, RouteSegment


@receiver(post_save, sender=Bus)
def on_bus_created(sender, instance, created, **kwargs):
    """
    Auto-generates seats when a new Bus is created.
    Row 1 = 3 seats, all subsequent rows = 5 seats each.
    """
    if created:
        from .helpers import generate_seats_for_bus
        generate_seats_for_bus(instance)


@receiver(post_save, sender=Route)
def on_route_created(sender, instance, created, **kwargs):
    """
    When a new non-reverse route is created:
    1. Auto-creates reverse route
    2. Auto-creates 2 initial stops (origin, destination)
    """
    if created and not instance.is_reverse:
        from .helpers import create_reverse_route
        create_reverse_route(instance)
        
        # Auto-create origin and destination stops
        RouteStop.objects.create(
            route=instance,
            name=instance.origin,
            order=1
        )
        RouteStop.objects.create(
            route=instance,
            name=instance.destination,
            order=2
        )


@receiver(post_save, sender=RouteStop)
def on_route_stop_changed(sender, instance, created, **kwargs):
    """
    When a forward route stop is updated/created, sync to reverse route.
    """
    route = instance.route
    if route and not route.is_reverse and route.reverse_route:
        from .helpers import sync_reverse_route_stops
        sync_reverse_route_stops(route)


@receiver(post_delete, sender=RouteStop)
def on_route_stop_deleted(sender, instance, **kwargs):
    """
    When a forward route stop is deleted, sync to reverse route.
    """
    route = instance.route
    if route and not route.is_reverse and route.reverse_route:
        from .helpers import sync_reverse_route_stops
        sync_reverse_route_stops(route)


@receiver(post_save, sender=Schedule)
def on_schedule_created(sender, instance, created, **kwargs):
    """
    Auto-sets available_seats from bus capacity when a schedule is created.
    """
    if created:
        Schedule.objects.filter(uid=instance.uid).update(
            available_seats=instance.bus.capacity
        )