"""
Business logic for affiliation checking.
"""

import logging
from typing import Dict, Any
from django.utils import timezone
from .models import AffiliationCheck
from infrastructure.external_apis.govcarpeta_client import get_govcarpeta_client

logger = logging.getLogger(__name__)


class AffiliationService:
    """Service for handling affiliation checks."""
    
    def __init__(self):
        self.api_client = get_govcarpeta_client()
    
    def check_affiliation(self, citizen_id: str) -> AffiliationCheck:
        """
        Check if a citizen is eligible for affiliation.
        
        Args:
            citizen_id: Citizen identification number
            
        Returns:
            AffiliationCheck: Database record with check results
            
        Raises:
            Exception: If there's an error during the check process
        """
        logger.info(f"Starting affiliation check for citizen_id: {citizen_id}")
        
        try:
            # Call external API to validate citizen
            api_response = self.api_client.validate_citizen(citizen_id)
            
            # Determine status based on API response
            # Business Logic:
            # - 204 (Not Found) → Citizen NOT affiliated yet → CAN create affiliation
            # - 200 (Found) → Citizen already affiliated → CANNOT create affiliation
            if api_response['exists']:
                # Citizen already exists in external system - CANNOT affiliate
                status = 'ALREADY_AFFILIATED'
                exists_in_system = True
                message = 'Citizen is already affiliated and cannot be registered again'
                citizen_data = api_response.get('citizen_data')
            else:
                # Citizen does NOT exist in external system - CAN affiliate
                status = 'ELIGIBLE'
                exists_in_system = False
                message = 'Citizen is not affiliated yet and can be registered'
                citizen_data = None
            
            # Create database record
            affiliation_check = AffiliationCheck.objects.create(
                citizen_id=citizen_id,
                status=status,
                exists_in_system=exists_in_system,
                citizen_data=citizen_data,
                message=message,
                checked_at=timezone.now(),
                external_api_status_code=api_response.get('status_code')
            )
            
            logger.info(
                f"Affiliation check completed for citizen_id: {citizen_id}, "
                f"status: {status}, exists: {exists_in_system}"
            )
            
            return affiliation_check
            
        except Exception as e:
            # Log the error
            logger.error(
                f"Error during affiliation check for citizen_id: {citizen_id}. "
                f"Error: {str(e)}",
                exc_info=True
            )
            
            # Create error record
            affiliation_check = AffiliationCheck.objects.create(
                citizen_id=citizen_id,
                status='ERROR',
                exists_in_system=False,
                citizen_data=None,
                message=f"Error during affiliation check: {str(e)}",
                checked_at=timezone.now(),
                external_api_status_code=None
            )
            
            # Re-raise the exception to be handled by the view
            raise
    
    def get_affiliation_history(self, citizen_id: str) -> list:
        """
        Get affiliation check history for a citizen.
        
        Args:
            citizen_id: Citizen identification number
            
        Returns:
            list: List of AffiliationCheck records ordered by most recent first
        """
        return AffiliationCheck.objects.filter(
            citizen_id=citizen_id
        ).order_by('-checked_at')
    
    def get_latest_check(self, citizen_id: str) -> AffiliationCheck | None:
        """
        Get the most recent affiliation check for a citizen.
        
        Args:
            citizen_id: Citizen identification number
            
        Returns:
            AffiliationCheck or None: Most recent check or None if not found
        """
        return AffiliationCheck.objects.filter(
            citizen_id=citizen_id
        ).order_by('-checked_at').first()
