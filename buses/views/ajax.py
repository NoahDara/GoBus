# buses/views.py - FIXED VERSION

from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from ..models import Schedule, Seat, RouteStop
from bookings.models import Booking
import logging

logger = logging.getLogger(__name__)


class ScheduleDetailAjaxView(LoginRequiredMixin, View):
    """
    AJAX: Get schedule details
    GET /buses/api/schedule/{uuid}/
    """
    
    def get(self, request, schedule_uid):
        try:
            schedule = Schedule.objects.get(uid=schedule_uid)
            
            # Get stops
            stops = RouteStop.objects.filter(
                route=schedule.route
            ).order_by('order').values('uid', 'name', 'order')
            
            # Get seats
            seats = Seat.objects.filter(
                bus=schedule.bus
            ).order_by('row', 'seat_number')
            
            # Get booked seat UIDs for this schedule
            booked_seat_uids = set(
                Booking.objects.filter(
                    schedule=schedule,
                    status='confirmed'
                ).values_list('seat__uid', flat=True)
            )
            
            # Format seats - USE seat.uid not seat.id
            seats_data = [
                {
                    'uid': str(seat.uid),
                    'row': seat.row,
                    'number': seat.seat_number,
                    'booked': seat.uid in booked_seat_uids  # ← FIX: use seat.uid
                }
                for seat in seats
            ]
            
            return JsonResponse({
                'success': True,
                'route': {
                    'origin': schedule.route.origin,
                    'destination': schedule.route.destination,
                    'name': schedule.route.name,
                },
                'stops': list(stops),
                'seats': seats_data,
                'bus': {
                    'capacity': schedule.bus.capacity,
                    'bus_number': schedule.bus.bus_number,
                }
            })
        
        except Schedule.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Schedule not found'}, status=404)
        except Exception as e:
            logger.error(f"Error fetching schedule: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


class FareCalculateAjaxView(LoginRequiredMixin, View):
    """
    AJAX: Calculate fare between stops
    GET /buses/api/fare/?schedule_uid=...&boarding_order=1&alighting_order=3
    """
    
    def get(self, request):
        schedule_uid = request.GET.get('schedule_uid')
        boarding_order = request.GET.get('boarding_order')
        alighting_order = request.GET.get('alighting_order')
        
        try:
            schedule = Schedule.objects.get(uid=schedule_uid)
            boarding_order = int(boarding_order)
            alighting_order = int(alighting_order)
            
            # Validate
            if boarding_order >= alighting_order:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid stop selection'
                }, status=400)
            
            # Calculate
            fare = schedule.route.calculate_fare(boarding_order, alighting_order)
            
            return JsonResponse({
                'success': True,
                'fare': float(fare),
                'currency': 'USD'
            })
        
        except Schedule.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Schedule not found'}, status=404)
        except Exception as e:
            logger.error(f"Fare calculation error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=400)