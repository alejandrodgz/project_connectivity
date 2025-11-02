"""
Management command to create service accounts for microservices.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import IntegrityError
import secrets


class Command(BaseCommand):
    help = 'Create a service account for microservice authentication'

    def add_arguments(self, parser):
        parser.add_argument(
            'service_name',
            type=str,
            help='Name of the service (e.g., document-auth-service)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='',
            help='Email for the service account'
        )

    def handle(self, *args, **options):
        service_name = options['service_name']
        email = options['email'] or f'{service_name}@services.internal'
        
        # Generate a secure password
        password = secrets.token_urlsafe(32)
        
        try:
            user = User.objects.create_user(
                username=service_name,
                email=email,
                password=password,
                is_staff=False,
                is_superuser=False
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Service account created successfully!'
            ))
            self.stdout.write(f'Service Name: {service_name}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'\n⚠️  SAVE THIS PASSWORD (shown only once):')
            self.stdout.write(self.style.WARNING(f'{password}'))
            self.stdout.write(f'\n💡 Use this to get JWT token:')
            self.stdout.write(f'curl -X POST http://your-api/api/token/ \\')
            self.stdout.write(f'  -H "Content-Type: application/json" \\')
            self.stdout.write(f'  -d \'{{"username": "{service_name}", "password": "{password}"}}\'')
            
        except IntegrityError:
            self.stdout.write(self.style.ERROR(
                f'❌ Service account "{service_name}" already exists!'
            ))
