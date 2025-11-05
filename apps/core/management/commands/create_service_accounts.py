"""
Management command to create service accounts for external services.

Service accounts are technical users that external services use to authenticate
and consume the API. They should have long-lived tokens and limited permissions.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
import os


class Command(BaseCommand):
    help = 'Create service accounts for external services (document-service, auth-service, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--service-name',
            type=str,
            help='Name of the service (e.g., document-service, auth-service)',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the service account',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the service account',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the service account',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Get from arguments or environment variables
        service_name = options.get('service_name') or os.environ.get('SERVICE_ACCOUNT_NAME')
        username = options.get('username') or os.environ.get('SERVICE_ACCOUNT_USERNAME')
        password = options.get('password') or os.environ.get('SERVICE_ACCOUNT_PASSWORD')
        email = options.get('email') or os.environ.get('SERVICE_ACCOUNT_EMAIL')

        if not all([service_name, username, password]):
            self.stdout.write(
                self.style.ERROR(
                    'Missing required parameters. Provide --service-name, --username, --password '
                    'or set SERVICE_ACCOUNT_NAME, SERVICE_ACCOUNT_USERNAME, SERVICE_ACCOUNT_PASSWORD '
                    'environment variables.'
                )
            )
            return

        # Create or get service accounts group
        service_group, created = Group.objects.get_or_create(name='service_accounts')
        if created:
            self.stdout.write(self.style.SUCCESS('✅ Created "service_accounts" group'))

        # Create or update service account user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email or f'{username}@system.local',
                'is_staff': False,  # Service accounts are not staff
                'is_superuser': False,  # Service accounts are not superusers
                'is_active': True,
                'first_name': service_name or 'Service',
                'last_name': 'Account',
            }
        )

        if created:
            user.set_password(password)
            user.groups.add(service_group)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Created service account: {username} (Service: {service_name})'
                )
            )
        else:
            # Update password for existing user
            user.set_password(password)
            user.groups.add(service_group)
            user.save()
            self.stdout.write(
                self.style.WARNING(
                    f'ℹ️  Service account already exists: {username} (password updated)'
                )
            )

        # Display credentials (only in development)
        if os.environ.get('DEBUG', 'False').lower() == 'true':
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('Service Account Credentials:'))
            self.stdout.write(f'  Service: {service_name}')
            self.stdout.write(f'  Username: {username}')
            self.stdout.write(f'  Password: {password}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write('\n' + '='*50)
