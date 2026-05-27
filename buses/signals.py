from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Bus, Route, Schedule


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
    Auto-creates a reverse route when a new non-reverse route is created.
    Skips reverse routes to prevent an infinite loop.
    e.g. Mutare → Masvingo triggers creation of Masvingo → Mutare.
    """
    if created and not instance.is_reverse:
        from .helpers import create_reverse_route
        create_reverse_route(instance)


@receiver(post_save, sender=Schedule)
def on_schedule_created(sender, instance, created, **kwargs):
    """
    Auto-sets available_seats from bus capacity when a schedule is created.
    """
    if created:
        Schedule.objects.filter(uid=instance.uid).update(
            available_seats=instance.bus.capacity
        )
  