# accounts/management/commands/generate_fake_data.py

"""
Django management command to generate fake data for GoBus.

Usage:
    python manage.py generate_fake_data
    python manage.py generate_fake_data --users 50 --buses 15 --bookings 200
    python manage.py generate_fake_data --clear
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from helpers.fake_data import FakeDataGenerator
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Generate fake data for GoBus application.
    """
    
    help = 'Generate fake data for testing and development'
    
    def add_arguments(self, parser):
        """Add command arguments"""
        
        # Data generation counts
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create (default: 20)'
        )
        
        parser.add_argument(
            '--routes',
            type=int,
            default=10,
            help='Number of routes to create (default: 10)'
        )
        
        parser.add_argument(
            '--buses',
            type=int,
            default=10,
            help='Number of buses to create (default: 10)'
        )
        
        parser.add_argument(
            '--drivers',
            type=int,
            default=8,
            help='Number of drivers to create (default: 8)'
        )
        
        parser.add_argument(
            '--schedules',
            type=int,
            default=50,
            help='Number of schedules to create (default: 50)'
        )
        
        parser.add_argument(
            '--bookings',
            type=int,
            default=100,
            help='Number of bookings to create (default: 100)'
        )
        
        # Options
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all data before generating'
        )
        
        parser.add_argument(
            '--no-admin',
            action='store_true',
            help='Do not create admin user'
        )
        
        parser.add_argument(
            '--seed',
            type=int,
            default=0,
            help='Random seed for reproducibility (default: 0)'
        )
    
    def handle(self, *args, **options):
        """Handle command execution"""
        
        # Get options
        users_count = options['users']
        routes_count = options['routes']
        buses_count = options['buses']
        drivers_count = options['drivers']
        schedules_count = options['schedules']
        bookings_count = options['bookings']
        clear_data = options['clear']
        include_admin = not options['no_admin']
        seed = options['seed']
        
        self.stdout.write(self.style.SUCCESS('\n🚌 GoBus Fake Data Generator\n'))
        
        # Clear data if requested
        if clear_data:
            self._clear_data()
        
        try:
            # Create generator
            generator = FakeDataGenerator()
            
            # Set seed if provided
            if seed:
                from faker import Faker
                Faker.seed(seed)
                self.stdout.write(f"🔧 Using seed: {seed}\n")
            
            # Generate data
            generator.generate_all(
                users=users_count,
                routes=routes_count,
                buses=buses_count,
                drivers=drivers_count,
                schedules=schedules_count,
                bookings=bookings_count
            )
            
            self.stdout.write(self.style.SUCCESS('\n✅ Fake data generated successfully!\n'))
            
            # Print test credentials
            self._print_test_credentials()
            
        except Exception as e:
            logger.error(f"Error generating fake data: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error: {str(e)}\n')
            )
            raise CommandError(f'Failed to generate fake data: {str(e)}')
    
    def _clear_data(self):
        """Clear existing data"""
        self.stdout.write(self.style.WARNING('\n🗑️  Clearing existing data...\n'))
        
        try:
            from buses.models import Bus, Route, Schedule, Seat
            from bookings.models import Booking
            from payments.models import Payment
            from drivers.models import Driver
            
            # Delete in order (respecting foreign keys)
            Booking.objects.all().delete()
            Payment.objects.all().delete()
            Schedule.objects.all().delete()
            Seat.objects.all().delete()
            Driver.objects.all().delete()
            Bus.objects.all().delete()
            Route.objects.all().delete()
            
            # Delete non-admin users
            User.objects.filter(is_staff=False, is_superuser=False).delete()
            
            self.stdout.write(self.style.SUCCESS('✅ Data cleared\n'))
        
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️  Could not clear some data: {str(e)}\n'))
    
    def _print_test_credentials(self):
        """Print test user credentials"""
        self.stdout.write(self.style.SUCCESS('\n📝 Test Credentials:\n'))
        
        print("Admin User:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Role: System Administrator")
        
        print("\nDriver User (if created):")
        driver_user = User.objects.filter(
            username__startswith='driver'
        ).first()
        if driver_user:
            print(f"  Username: {driver_user.username}")
            print(f"  Password: testpass123")
            print(f"  Name: {driver_user.first_name} {driver_user.last_name}")
            print("  Role: Bus Driver")
        
        print("\nPassenger User (if created):")
        passenger = User.objects.filter(
            is_staff=False,
            is_superuser=False
        ).exclude(
            username__startswith='driver'
        ).first()
        if passenger:
            print(f"  Username: {passenger.username}")
            print(f"  Password: testpass123")
            print(f"  Name: {passenger.first_name} {passenger.last_name}")
            print("  Role: Passenger")
        
        print("\n" + "="*50 + "\n")