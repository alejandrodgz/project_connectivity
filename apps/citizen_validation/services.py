"""
Service for validating citizen existence in external centralizer.

CORE FUNCTIONALITY #1: Query external API and track communication.
"""

import logging
from django.utils import timezone
from .models import CitizenValidationTrace
from infrastructure.external_apis.govcarpeta_client import get_govcarpeta_client

logger = logging.getLogger(__name__)


class CitizenValidationService:
    """
    Service for validating citizen existence in external centralizer.
    
    This service does NOT store citizen data, it only:
    1. Queries external centralizer API
    2. Returns the result
    3. Tracks the communication (traceability)
    """
    
    def __init__(self):
        self.api_client = get_govcarpeta_client()
    
    def validate_citizen(self, citizen_id: str) -> CitizenValidationTrace:
        """
        Query external centralizer to check if citizen exists.
        
        Business Logic:
        - API returns 204 → Citizen NOT in centralizer (can register)
        - API returns 200 → Citizen EXISTS in centralizer (cannot register)
        
        Args:
            citizen_id: Citizen ID to validate
            
        Returns:
            CitizenValidationTrace: Communication trace record
        """
        logger.info(f"Querying centralizer for citizen {citizen_id}")
        
        try:
            api_response = self.api_client.validate_citizen(citizen_id)
            
            if api_response['exists']:
                status = 'EXISTS'
            else:
                status = 'NOT_EXISTS'
            
            trace = CitizenValidationTrace.objects.create(
                citizen_id=citizen_id,
                status=status,
                requested_at=timezone.now(),
                external_api_status_code=api_response.get('status_code')
            )
            
            logger.info(f"Citizen {citizen_id} validation: {status}")
            return trace
            
        except Exception as e:
            logger.error(f"Error querying centralizer for citizen {citizen_id}: {str(e)}", exc_info=True)
            
            trace = CitizenValidationTrace.objects.create(
                citizen_id=citizen_id,
                status='ERROR',
                requested_at=timezone.now(),
                error_message=str(e)
            )
            raise
