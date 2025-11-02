"""
Management command to create service accounts for external services.
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
import secrets
import string


class Command(BaseCommand):
    help = 'Create a service account for external service authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            'service_name',
            type=str,
            help='Name of the external service (e.g., payment-service)'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Custom password (if not provided, one will be generated)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='',
            help='Email address for the service account'
        )

    def handle(self, *args, **options):
        service_name = options['service_name']
        password = options['password']
        email = options['email']

        # Generate secure password if not provided
        if not password:
            alphabet = string.ascii_letters + string.digits + '!@#$%^&*'
            password = ''.join(secrets.choice(alphabet) for _ in range(24))

        # Check if user already exists
        if User.objects.filter(username=service_name).exists():
            raise CommandError(f'Service account "{service_name}" already exists')

        # Create service account
        user = User.objects.create_user(
            username=service_name,
            password=password,
            email=email,
            is_active=True,
            is_staff=False,
            is_superuser=False
        )

        # Display credentials
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('SERVICE ACCOUNT CREATED SUCCESSFULLY'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'\nService Name: {service_name}')
        self.stdout.write(f'Username:     {user.username}')
        self.stdout.write(f'Password:     {password}')
        if email:
            self.stdout.write(f'Email:        {email}')
        
        self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANT: Save these credentials securely!'))
        self.stdout.write(self.style.WARNING('   This is the only time the password will be displayed.'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write('\nProvide these credentials to the external service:')
        self.stdout.write(f'\n  Username: {user.username}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write('\n  Token Endpoint: POST /api/v1/token/')
        self.stdout.write('  Affiliation Endpoint: POST /api/v1/affiliation/check/')
        self.stdout.write(self.style.SUCCESS('\n' + '='*70 + '\n'))
