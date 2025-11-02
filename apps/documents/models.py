"""
Models for document authentication.
"""

from django.db import models
from django.utils import timezone


class DocumentAuthentication(models.Model):
    """Record of document authentication attempts."""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Authenticated Successfully'),
        ('FAILED', 'Authentication Failed'),
        ('ERROR', 'Error During Processing'),
    ]
    
    # Citizen and document information
    id_citizen = models.BigIntegerField(db_index=True)
    url_document = models.URLField(max_length=500)
    document_title = models.CharField(max_length=200)
    
    # Authentication result
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    auth_success = models.BooleanField(default=False)
    
    # External API response
    external_api_status_code = models.IntegerField(null=True, blank=True)
    external_api_response = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    received_at = models.DateTimeField(default=timezone.now, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    event_published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'document_authentications'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['id_citizen', '-received_at']),
            models.Index(fields=['status', '-received_at']),
        ]
        verbose_name = 'Document Authentication'
        verbose_name_plural = 'Document Authentications'
    
    def __str__(self):
        return f"Doc Auth - Citizen {self.id_citizen} - {self.document_title} - {self.status}"
    
    def mark_as_success(self, status_code: int, response_data: dict = None):
        """Mark authentication as successful."""
        self.status = 'SUCCESS'
        self.auth_success = True
        self.external_api_status_code = status_code
        self.external_api_response = response_data
        self.processed_at = timezone.now()
        self.save()
    
    def mark_as_failed(self, status_code: int = None, error_message: str = '', response_data: dict = None):
        """Mark authentication as failed."""
        self.status = 'FAILED'
        self.auth_success = False
        self.external_api_status_code = status_code
        self.external_api_response = response_data
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save()
    
    def mark_as_error(self, error_message: str):
        """Mark as error during processing."""
        self.status = 'ERROR'
        self.auth_success = False
        self.error_message = error_message
        self.processed_at = timezone.now()
        self.save()
    
    def mark_event_published(self):
        """Mark that result event was published."""
        self.event_published_at = timezone.now()
        self.save(update_fields=['event_published_at'])
