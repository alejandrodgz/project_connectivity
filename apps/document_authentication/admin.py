from django.contrib import admin
from .models import DocumentAuthenticationTrace


@admin.register(DocumentAuthenticationTrace)
class DocumentAuthenticationTraceAdmin(admin.ModelAdmin):
    """Admin for document authentication communication traces."""
    
    list_display = ['id_citizen', 'document_title', 'status', 'auth_success', 
                   'received_at', 'sent_at', 'event_published_at']
    list_filter = ['status', 'auth_success', 'received_at']
    search_fields = ['id_citizen', 'document_title']
    readonly_fields = ['id_citizen', 'document_title', 'status', 'auth_success',
                      'received_at', 'sent_at', 'event_published_at',
                      'external_api_status_code', 'error_message']
    ordering = ['-received_at']
