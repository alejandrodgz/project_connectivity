"""
Models for citizen affiliation checking.
"""

from django.db import models
from django.utils import timezone


class AffiliationCheck(models.Model):
    """Record of affiliation eligibility checks."""
    
    STATUS_CHOICES = [
        ('ELIGIBLE', 'Eligible for Affiliation'),
        ('ALREADY_AFFILIATED', 'Already Affiliated'),
        ('NOT_FOUND', 'Citizen Not Found'),
        ('ERROR', 'Error'),
    ]
    
    # Citizen information
    citizen_id = models.CharField(max_length=50, db_index=True)
    
    # Check result
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    exists_in_system = models.BooleanField(default=False)
    
    # External API response
    citizen_data = models.JSONField(null=True, blank=True, help_text="Data returned from external API")
    message = models.TextField(blank=True)
    
    # Metadata
    checked_at = models.DateTimeField(default=timezone.now, db_index=True)
    external_api_status_code = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'affiliation_checks'
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['citizen_id', '-checked_at']),
            models.Index(fields=['status', '-checked_at']),
        ]
        verbose_name = 'Affiliation Check'
        verbose_name_plural = 'Affiliation Checks'

    def __str__(self):
        return f"Affiliation Check - {self.citizen_id} - {self.status}"

    @property
    def is_eligible(self) -> bool:
        """
        Check if the citizen is eligible for affiliation.
        
        Business Logic:
        - ELIGIBLE status = Citizen NOT in external system = CAN create affiliation
        - ALREADY_AFFILIATED = Citizen in external system = CANNOT create affiliation
        """
        return self.status == 'ELIGIBLE'

