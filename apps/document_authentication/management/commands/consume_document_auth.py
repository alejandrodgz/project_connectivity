"""
Management command to start the document authentication consumer.
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings

from infrastructure.rabbitmq.consumer import create_document_auth_consumer
from apps.document_authentication.services import DocumentAuthenticationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Start RabbitMQ consumer for document authentication events'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--routing-key',
            type=str,
            default='document.authentication.requested',
            help='Routing key to listen to (default: document.authentication.requested)'
        )
    
    def handle(self, *args, **options):
        routing_key = options['routing_key']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('DOCUMENT AUTHENTICATION CONSUMER'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'\nListening to routing key: {routing_key}')
        self.stdout.write(f'Exchange: {getattr(settings, "RABBITMQ_EXCHANGE", "citizen_affiliation")}')
        self.stdout.write(self.style.SUCCESS('\nPress CTRL+C to stop\n'))
        self.stdout.write('='*70 + '\n')
        
        # Create service instance
        service = DocumentAuthenticationService()
        
        # Define callback function
        def process_message(message: dict):
            """Process incoming document authentication request."""
            try:
                id_citizen = message.get('idCitizen')
                url_document = message.get('UrlDocument')
                document_title = message.get('documentTitle')
                
                if not all([id_citizen, url_document, document_title]):
                    self.stdout.write(
                        self.style.ERROR(
                            f'Invalid message format. Missing required fields: {message}'
                        )
                    )
                    return
                
                self.stdout.write(
                    f'\n📄 Processing document for citizen {id_citizen}: {document_title}'
                )
                
                # Process authentication
                result = service.process_authentication_request(
                    id_citizen=id_citizen,
                    url_document=url_document,
                    document_title=document_title
                )
                
                if result.auth_success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Authentication successful for citizen {id_citizen}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'❌ Authentication failed for citizen {id_citizen}: '
                            f'{result.error_message}'
                        )
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error processing message: {str(e)}'
                    )
                )
                logger.error(f'Error processing message: {str(e)}', exc_info=True)
        
        # Create and start consumer
        consumer = create_document_auth_consumer(callback=process_message)
        
        try:
            consumer.start_consuming()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n\nStopping consumer...'))
            consumer.stop_consuming()
            self.stdout.write(self.style.SUCCESS('Consumer stopped successfully\n'))
