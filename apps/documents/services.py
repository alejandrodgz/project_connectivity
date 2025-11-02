"""
Business logic for document authentication.
"""

import logging
from typing import Dict, Any
from django.utils import timezone

from .models import DocumentAuthentication
from infrastructure.external_apis.govcarpeta_client import get_govcarpeta_client
from infrastructure.rabbitmq.producer import get_rabbitmq_producer

logger = logging.getLogger(__name__)


class DocumentAuthenticationService:
    """Service for handling document authentication via external API and RabbitMQ."""
    
    def __init__(self):
        self.api_client = get_govcarpeta_client()
        self.rabbitmq_producer = get_rabbitmq_producer()
    
    def process_authentication_request(
        self,
        id_citizen: int,
        url_document: str,
        document_title: str
    ) -> DocumentAuthentication:
        """
        Process a document authentication request.
        
        Workflow:
        1. Create database record
        2. Call external API to authenticate document
        3. Update record with result
        4. Publish result event to RabbitMQ
        
        Args:
            id_citizen: Citizen identification number
            url_document: URL to the document (S3 URL)
            document_title: Title/type of the document
            
        Returns:
            DocumentAuthentication: Database record with authentication result
        """
        logger.info(
            f"Processing document authentication for citizen {id_citizen}: {document_title}"
        )
        
        # Step 1: Create database record
        doc_auth = DocumentAuthentication.objects.create(
            id_citizen=id_citizen,
            url_document=url_document,
            document_title=document_title,
            status='PENDING'
        )
        
        try:
            # Step 2: Call external API
            api_response = self.api_client.authenticate_document(
                id_citizen=id_citizen,
                url_document=url_document,
                document_title=document_title
            )
            
            # Step 3: Update record based on response
            if api_response['success'] and api_response['status_code'] == 200:
                doc_auth.mark_as_success(
                    status_code=api_response['status_code'],
                    response_data=api_response.get('data')
                )
                logger.info(
                    f"Document authenticated successfully for citizen {id_citizen}"
                )
            else:
                doc_auth.mark_as_failed(
                    status_code=api_response.get('status_code'),
                    error_message=api_response.get('message', 'Authentication failed'),
                    response_data=api_response.get('data')
                )
                logger.warning(
                    f"Document authentication failed for citizen {id_citizen}: "
                    f"{api_response.get('message')}"
                )
            
            # Step 4: Publish result event
            self._publish_result_event(doc_auth)
            
            return doc_auth
            
        except Exception as e:
            logger.error(
                f"Error processing document authentication for citizen {id_citizen}: {str(e)}",
                exc_info=True
            )
            
            doc_auth.mark_as_error(error_message=str(e))
            
            # Try to publish error event
            try:
                self._publish_result_event(doc_auth)
            except Exception as publish_error:
                logger.error(
                    f"Failed to publish error event for citizen {id_citizen}: {str(publish_error)}"
                )
            
            raise
    
    def _publish_result_event(self, doc_auth: DocumentAuthentication):
        """
        Publish document authentication result event to RabbitMQ.
        
        Event format:
        {
            "idCitizen": 1234567890,
            "UrlDocument": "https://...",
            "documentTitle": "Diploma Grado",
            "authSuccess": true/false
        }
        """
        event_data = {
            "idCitizen": doc_auth.id_citizen,
            "UrlDocument": doc_auth.url_document,
            "documentTitle": doc_auth.document_title,
            "authSuccess": doc_auth.auth_success
        }
        
        # Determine routing key based on success/failure
        if doc_auth.auth_success:
            routing_key = 'document.auth.success'
        else:
            routing_key = 'document.auth.failure'
        
        try:
            self.rabbitmq_producer.publish_event(
                routing_key=routing_key,
                event_data=event_data
            )
            
            doc_auth.mark_event_published()
            
            logger.info(
                f"Published {routing_key} event for citizen {doc_auth.id_citizen}"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to publish result event for citizen {doc_auth.id_citizen}: {str(e)}",
                exc_info=True
            )
            raise
    
    def get_authentication_history(self, id_citizen: int) -> list:
        """
        Get document authentication history for a citizen.
        
        Args:
            id_citizen: Citizen identification number
            
        Returns:
            list: List of DocumentAuthentication records
        """
        return DocumentAuthentication.objects.filter(id_citizen=id_citizen)
