# helpers/fake_data.py

"""
Generate random/fake data for testing and development.
FIXED to match actual GoBus models.

Usage:
    python manage.py generate_fake_data
    python manage.py generate_fake_data --users 50 --buses 10 --bookings 100
"""

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
import logging
from decimal import Decimal
from faker import Faker

logger = logging.getLogger(__name__)

fake = Faker()
Faker.seed(0)  # For reproducibility


class FakeDataGenerator:
    """Generate fake data for all GoBus models"""
    
    def __init__(self):
        self.fake = fake
    
    # ════════════════════════════════════════════════════════════════
    # USERS & ACCOUNTS
    # ════════════════════════════════════════════════════════════════
    
    def generate_users(self, count=20, include_admin=True):
        """Generate random users (passengers, drivers, admins)."""
        print(f"📝 Generating {count} users...")
        users = []
        
        # Create admin user if requested
        if include_admin:
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={
                    'email': 'admin@gobus.com',
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'is_staff': True,
                    'is_superuser': True,
                }
            )
            if created:
                admin_user.set_password('admin123')
                admin_user.save()
                users.append(admin_user)
                print(f"✅ Created admin user: admin@gobus.com")
        
        # Create regular users
        for i in range(count):
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 999)}"
            email = f"{username}@example.com"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            if created:
                user.set_password('testpass123')
                user.save()
                users.append(user)
        
        print(f"✅ Created {len(users)} users")
        return users
    
    # ════════════════════════════════════════════════════════════════
    # ROUTES WITH STOPS AND SEGMENTS
    # ════════════════════════════════════════════════════════════════
    
    def generate_routes(self, count=10):
        """Generate random routes with stops and segments."""
        from buses.models import Route, RouteStop, RouteSegment
        
        print(f"🛣️  Generating {count} routes with stops and segments...")
        
        cities = [
            'Harare', 'Bulawayo', 'Chitungwiza', 'Mutare', 'Gweru',
            'Kwekwe', 'Norton', 'Masvingo', 'Chinhoyi', 'Zvishavane'
        ]
        
        routes = []
        
        for i in range(count):
            origin = random.choice(cities)
            destination = random.choice([c for c in cities if c != origin])
            
            route_name = f"{origin} - {destination}"
            
            # Create forward route
            route_fwd, created = Route.objects.get_or_create(
                name=route_name,
                origin=origin,
                destination=destination,
                is_reverse=False,
                defaults={
                    'estimated_duration': timedelta(hours=random.randint(1, 8)),
                }
            )
            
            if created:
                routes.append(route_fwd)
                
                # Create 3-5 stops for this route
                num_stops = random.randint(3, 5)
                stops = []
                
                # Create origin stop
                origin_stop, _ = RouteStop.objects.get_or_create(
                    route=route_fwd,
                    order=1,
                    defaults={'name': origin}
                )
                stops.append(origin_stop)
                
                # Create intermediate stops
                for stop_order in range(2, num_stops):
                    stop_name = f"{origin} - Stop {stop_order}"
                    stop, _ = RouteStop.objects.get_or_create(
                        route=route_fwd,
                        order=stop_order,
                        defaults={'name': stop_name}
                    )
                    stops.append(stop)
                
                # Create destination stop
                dest_stop, _ = RouteStop.objects.get_or_create(
                    route=route_fwd,
                    order=num_stops,
                    defaults={'name': destination}
                )
                stops.append(dest_stop)
                
                # Create segments between consecutive stops
                for j in range(len(stops) - 1):
                    from_stop = stops[j]
                    to_stop = stops[j + 1]
                    
                    segment, created = RouteSegment.objects.get_or_create(
                        route=route_fwd,
                        from_stop=from_stop,
                        to_stop=to_stop,
                        defaults={
                            'price': Decimal(random.randint(100, 500))
                        }
                    )
            
            # Create reverse route (auto-created by signal in real system)
            # But we'll create it manually here
            route_rev, created = Route.objects.get_or_create(
                name=f"{destination} - {origin}",
                origin=destination,
                destination=origin,
                is_reverse=True,
                defaults={
                    'estimated_duration': route_fwd.estimated_duration,
                    'reverse_of': route_fwd,
                }
            )
            
            if created:
                routes.append(route_rev)
                
                # Create stops for reverse route (in reverse order)
                fwd_stops = list(RouteStop.objects.filter(route=route_fwd).order_by('order'))
                
                for stop_order, fwd_stop in enumerate(reversed(fwd_stops), 1):
                    rev_stop, _ = RouteStop.objects.get_or_create(
                        route=route_rev,
                        order=stop_order,
                        defaults={'name': fwd_stop.name}
                    )
                
                # Create segments for reverse route
                rev_stops = list(RouteStop.objects.filter(route=route_rev).order_by('order'))
                for j in range(len(rev_stops) - 1):
                    from_stop = rev_stops[j]
                    to_stop = rev_stops[j + 1]
                    
                    segment, created = RouteSegment.objects.get_or_create(
                        route=route_rev,
                        from_stop=from_stop,
                        to_stop=to_stop,
                        defaults={
                            'price': Decimal(random.randint(100, 500))
                        }
                    )
        
        print(f"✅ Created {len(routes)} routes with stops and segments")
        return routes
    
    # ════════════════════════════════════════════════════════════════
    # BUSES
    # ════════════════════════════════════════════════════════════════
    
    def generate_buses(self, count=10):
        """Generate random buses."""
        from buses.models import Bus
        
        print(f"🚌 Generating {count} buses...")
        
        bus_models = ['Volvo', 'Mercedes', 'Scania', 'Hino', 'Man']
        buses = []
        
        for i in range(count):
            bus_number = f"BUS{random.randint(1000, 9999)}"
            plate_number = f"{random.choice(['ZW', 'HY', 'BW'])}{random.randint(100000, 999999)}"
            
            bus, created = Bus.objects.get_or_create(
                bus_number=bus_number,
                defaults={
                    'plate_number': plate_number,
                    'capacity': random.choice([45, 50, 55, 60]),
                    'is_operational': random.choice([True, True, True, False]),  # 75% operational
                }
            )
            
            if created:
                buses.append(bus)
        
        print(f"✅ Created {len(buses)} buses")
        return buses
    
    # ════════════════════════════════════════════════════════════════
    # DRIVERS
    # ════════════════════════════════════════════════════════════════
    
    def generate_drivers(self, user_count=10, bus_count=None):
        """Generate random drivers and assign to buses."""
        from drivers.models import Driver
        from buses.models import Bus
        
        print(f"👨‍✈️  Generating {user_count} drivers...")
        
        drivers_list = []
        
        for i in range(user_count):
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            username = f"driver{i}{random.randint(1, 999)}"
            email = f"{first_name.lower()}.{last_name.lower()}@driver.com"
            
            # Create or get user
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            user.set_password('testpass123')  
            user.save()
            
            if not hasattr(user, 'driver'):
                # Create driver profile
                license_expiry = timezone.now() + timedelta(days=random.randint(100, 1000))
                
                driver, created = Driver.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'phone_number': self.fake.phone_number()[:15],
                        'license_number': f"DL{random.randint(100000, 999999)}",
                        'license_expiry': license_expiry,
                        'date_of_birth': self.fake.date_of_birth(minimum_age=25, maximum_age=65),
                        'gender': random.choice(['male', 'female', 'other']),
                        'address': self.fake.address(),
                    }
                )
                
                if created:
                    drivers_list.append(driver)
        
        # Assign drivers to buses
        buses = Bus.objects.filter(is_operational=True)[:bus_count] if bus_count else Bus.objects.filter(is_operational=True)
        
        for driver in drivers_list:
            if buses.exists():
                bus = random.choice(list(buses))
                bus.driver = driver
                bus.save()
        
        print(f"✅ Created {len(drivers_list)} drivers and assigned to buses")
        return drivers_list
    
    # ════════════════════════════════════════════════════════════════
    # SCHEDULES
    # ════════════════════════════════════════════════════════════════
    
    def generate_schedules(self, count=50):
        """Generate random bus schedules."""
        from buses.models import Schedule, Bus, Route
        
        print(f"📅 Generating {count} schedules...")
        
        buses = Bus.objects.filter(is_operational=True)
        routes = Route.objects.filter(is_reverse=False)
        
        if not buses.exists() or not routes.exists():
            print("⚠️  No operational buses or routes available.")
            return []
        
        schedules = []
        now = timezone.now()
        
        for i in range(count):
            bus = random.choice(list(buses))
            route = random.choice(list(routes))
            
            # Random departure time (next 30 days)
            departure_date = now + timedelta(days=random.randint(0, 30))
            departure_hour = random.choice([6, 8, 10, 12, 14, 16, 18, 20])
            departure_time = departure_date.replace(hour=departure_hour, minute=0, second=0)
            
            # Calculate arrival time
            arrival_time = departure_time + route.estimated_duration
            
            schedule, created = Schedule.objects.get_or_create(
                bus=bus,
                route=route,
                departure_time=departure_time,
                defaults={
                    'arrival_time': arrival_time,
                    'status': 'scheduled',
                    'available_seats': bus.capacity,
                }
            )
            
            if created:
                schedules.append(schedule)
        
        print(f"✅ Created {len(schedules)} schedules")
        return schedules
    
    # ════════════════════════════════════════════════════════════════
    # BOOKINGS
    # ════════════════════════════════════════════════════════════════
    
    def generate_bookings(self, count=100):
        """Generate random bookings for passengers."""
        from bookings.models import Booking
        from buses.models import Schedule, Seat, RouteStop
        from django.contrib.auth.models import User
        import uuid
        
        print(f"🎫 Generating {count} bookings...")
        
        schedules = Schedule.objects.all()
        passengers = User.objects.filter(is_staff=False, is_superuser=False)[:50]
        
        if not schedules.exists() or not passengers.exists():
            print("⚠️  No schedules or passengers available.")
            return []
        
        bookings = []
        
        for i in range(count):
            schedule = random.choice(list(schedules))
            passenger = random.choice(list(passengers))
            
            # Get available seats
            available_seats = Seat.objects.filter(bus=schedule.bus)
            
            if not available_seats.exists():
                continue
            
            seat = random.choice(list(available_seats))
            
            # Get boarding and alighting stops
            stops = list(RouteStop.objects.filter(route=schedule.route).order_by('order'))
            if len(stops) < 2:
                continue
            
            boarding_stop = stops[0]
            alighting_stop = stops[random.randint(1, len(stops) - 1)]
            
            # Calculate fare using route's calculate_fare method
            try:
                fare = schedule.route.calculate_fare(
                    boarding_stop.order,
                    alighting_stop.order
                )
            except:
                fare = Decimal(random.randint(100, 500))
            
            # Generate booking reference
            booking_ref = f"BK{str(uuid.uuid4())[:10].upper()}"
            
            booking, created = Booking.objects.get_or_create(
                user=passenger,
                schedule=schedule,
                seat=seat,
                defaults={
                    'booking_reference': booking_ref,
                    'fare': fare if fare > 0 else Decimal(random.randint(100, 500)),
                    'status': random.choice(['pending', 'confirmed', 'confirmed', 'confirmed']),  # 75% confirmed
                    'boarding_stop': boarding_stop,
                    'alighting_stop': alighting_stop,
                    'created': timezone.now() - timedelta(days=random.randint(0, 30)),
                }
            )
            
            if created:
                bookings.append(booking)
                
                # Decrement available seats on schedule
                if booking.status == 'confirmed':
                    schedule.available_seats -= 1
                    schedule.save(update_fields=['available_seats'])
        
        print(f"✅ Created {len(bookings)} bookings")
        return bookings
    
    # ════════════════════════════════════════════════════════════════
    # PAYMENTS
    # ════════════════════════════════════════════════════════════════
    
    def generate_payments(self):
        """Generate payments for confirmed bookings."""
        from payments.models import Payment
        from bookings.models import Booking
        import uuid
        
        print(f"💰 Generating payments for confirmed bookings...")
        
        confirmed_bookings = Booking.objects.filter(status='confirmed')
        payments = []
        
        for booking in confirmed_bookings:
            if Payment.objects.filter(booking=booking).exists():
                continue
            
            payment_ref = f"PAY{str(uuid.uuid4())[:10].upper()}"
            poll_url = f"https://api.paynow.co.zw/poll/{payment_ref}"
            
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'user': booking.user,
                    'amount': booking.fare,
                    'phone_number': f"077{random.randint(1000000, 9999999)}",
                    'payment_reference': payment_ref,
                    'poll_url': poll_url,
                    'status': random.choice(['paid', 'paid', 'pending']),  # 67% paid
                    'paynow_status': 'Paid' if random.choice([True, True, False]) else 'Pending',
                    'created': timezone.now() - timedelta(days=random.randint(0, 30)),
                    'confirmed_at': timezone.now() - timedelta(days=random.randint(0, 30)) if random.choice([True, False]) else None,
                    'metadata': {'route': booking.schedule.route.name, 'bus': booking.schedule.bus.bus_number},
                }
            )
            
            if created:
                payments.append(payment)
                
                # If payment is paid, update booking status
                if payment.status == 'paid':
                    booking.status = 'confirmed'
                    booking.save(update_fields=['status'])
        
        print(f"✅ Created {len(payments)} payments")
        return payments
    
    # ════════════════════════════════════════════════════════════════
    # MAIN GENERATOR
    # ════════════════════════════════════════════════════════════════
    
    def generate_all(self, users=20, routes=10, buses=10, drivers=8, schedules=50, bookings=100):
        """Generate all fake data."""
        print("\n" + "="*60)
        print("🚀 GENERATING FAKE DATA FOR GOBUS")
        print("="*60 + "\n")
        
        try:
            self.generate_users(count=users)
            self.generate_routes(count=routes)
            self.generate_buses(count=buses)
            self.generate_drivers(user_count=drivers, bus_count=buses//2)
            self.generate_schedules(count=schedules)
            self.generate_bookings(count=bookings)
            self.generate_payments()
            
            print("\n" + "="*60)
            print("✅ FAKE DATA GENERATION COMPLETE!")
            print("="*60 + "\n")
            
            # Print summary
            from django.contrib.auth.models import User
            from buses.models import Route, Bus, Schedule, Seat
            from bookings.models import Booking
            from payments.models import Payment
            from drivers.models import Driver
            
            print("📊 Summary:")
            print(f"   Users: {User.objects.count()}")
            print(f"   Routes: {Route.objects.count()}")
            print(f"   Buses: {Bus.objects.count()}")
            print(f"   Drivers: {Driver.objects.count()}")
            print(f"   Schedules: {Schedule.objects.count()}")
            print(f"   Bookings: {Booking.objects.count()}")
            print(f"   Payments: {Payment.objects.count()}")
            
            print("\n🎉 Ready for testing!\n")
            
        except Exception as e:
            logger.error(f"Error generating fake data: {str(e)}")
            print(f"❌ Error: {str(e)}")
            raise


def generate_fake_data(**kwargs):
    """Main function to generate fake data."""
    generator = FakeDataGenerator()
    generator.generate_all(**kwargs)


if __name__ == '__main__':
    generate_fake_data()