"""
Service for forwarding document authentication to external centralizer.

CORE FUNCTIONALITY #3: Forward authentication requests (proxy).
"""

import logging
from django.utils import timezone

from .models import DocumentAuthenticationTrace
from infrastructure.external_apis.govcarpeta_client import get_govcarpeta_client
from infrastructure.rabbitmq.producer import get_rabbitmq_producer

logger = logging.getLogger(__name__)


class DocumentAuthenticationService:
    """
    Service for forwarding document authentication to external centralizer.
    
    This service does NOT store documents, it only:
    1. Receives authentication request
    2. Forwards to external centralizer API
    3. Publishes result event
    4. Tracks the communication (traceability)
    """
    
    def __init__(self):
        self.api_client = get_govcarpeta_client()
        self.rabbitmq_producer = get_rabbitmq_producer()
    
    def process_authentication_request(
        self,
        id_citizen: int,
        url_document: str,
        document_title: str
    ) -> DocumentAuthenticationTrace:
        """
        Forward document authentication to external centralizer.
        
        Workflow:
        1. Create trace record
        2. Forward to external API
        3. Update trace
        4. Publish result event
        """
        logger.info(f"Forwarding authentication for citizen {id_citizen}: {document_title}")
        
        trace = DocumentAuthenticationTrace.objects.create(
            id_citizen=id_citizen,
            document_title=document_title,
            status='PENDING'
        )
        
        try:
            api_response = self.api_client.authenticate_document(
                id_citizen=id_citizen,
                url_document=url_document,
                document_title=document_title
            )
            
            success = api_response['success'] and api_response['status_code'] == 200
            trace.mark_as_sent(
                status_code=api_response['status_code'],
                success=success
            )
            
            logger.info(f"Authentication request sent for citizen {id_citizen}, success: {success}")
            
            self._publish_result_event(trace, url_document)
            return trace
            
        except Exception as e:
            logger.error(f"Error forwarding authentication for citizen {id_citizen}: {str(e)}", exc_info=True)
            trace.mark_as_error(error_message=str(e))
            
            try:
                self._publish_result_event(trace, url_document)
            except Exception as publish_error:
                logger.error(f"Failed to publish error event: {str(publish_error)}")
            
            raise
    
    def _publish_result_event(self, trace: DocumentAuthenticationTrace, url_document: str):
        """Publish authentication result to RabbitMQ."""
        event_data = {
            "idCitizen": trace.id_citizen,
            "UrlDocument": url_document,
            "documentTitle": trace.document_title,
            "authSuccess": trace.auth_success
        }
        
        routing_key = 'document.authentication.ready' if trace.auth_success else 'document.auth.failure'
        
        try:
            self.rabbitmq_producer.publish_event(
                routing_key=routing_key,
                event_data=event_data
            )
            trace.mark_event_published()
            logger.info(f"Published {routing_key} for citizen {trace.id_citizen}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}", exc_info=True)
            raise
